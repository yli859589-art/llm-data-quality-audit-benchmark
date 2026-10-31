"""Shared business logic used by the P2-1 CLI, worker, and local web app."""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from collections import Counter
from collections.abc import Iterator
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data.scalable_pipeline import PipelineConfig, iter_records, run_resumable_pipeline, sha256_file
from data.token_counting import count_tokens
from filters_v2.base import FilterConfig, FilterInput
from filters_v2.registry import get_filter_class

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
SYSTEM_VERSION = "p2-01.system.v1"

STRATEGIES: dict[str, dict[str, Any]] = {
    "raw": {
        "label": "Raw",
        "description": "不做质量拒绝；使用 P1-2 可恢复流式复制。",
        "streaming": True,
    },
    "exact_dedup": {"label": "Exact Dedup", "description": "调用现有精确去重筛选器。"},
    "minhash_lsh_near_dedup": {
        "label": "MinHash/LSH Near Dedup",
        "description": "调用现有 MinHash/LSH 候选检索与精确 shingle 确认。",
    },
    "length_filter": {"label": "Length Filter", "description": "调用现有长度阈值筛选器。"},
    "c4_style_proxy": {
        "label": "C4/Gopher 风格质量筛选",
        "description": "调用项目 C4 风格代理质量筛选器；不是官方复现。",
        "proxy": True,
    },
    "gopher_style_proxy": {
        "label": "Gopher 风格质量筛选",
        "description": "调用项目 Gopher 风格代理质量筛选器；不是官方复现。",
        "proxy": True,
    },
    "perplexity_proxy": {
        "label": "Perplexity Proxy",
        "description": "调用项目可解释的困惑度代理；不是预训练 LM PPL。",
        "proxy": True,
    },
    "urd_fixed": {
        "label": "URD-Selector",
        "description": "调用项目现有多目标 URD 固定权重选择器。",
        "proxy": True,
    },
    "random_same_keep_rate": {
        "label": "Random Token-Matched 控制",
        "description": "调用现有随机同保留率控制；通用入口不宣称逐 token 精确匹配。",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


class TaskStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS tasks "
                "(task_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )

    def put(self, payload: dict[str, Any]) -> None:
        payload["updated_at"] = _now()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO tasks VALUES (?,?,?)",
                (payload["task_id"], json.dumps(payload, sort_keys=True), payload["updated_at"]),
            )

    def get(self, task_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT payload FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if not row:
            raise KeyError(f"unknown task: {task_id}")
        return json.loads(str(row[0]))

    def list(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                "SELECT payload FROM tasks ORDER BY updated_at DESC"
            ).fetchall()
        return [json.loads(str(row[0])) for row in rows]


class QualitySystemService:
    """Version-isolated orchestration that calls existing P0/P1 modules."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.output_root = self.root / "artifacts" / "p2_01_system"
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.catalog_path = self.output_root / "datasets.json"
        self.tasks = TaskStore(self.output_root / "tasks.sqlite")

    def _inside_output(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.output_root.resolve())
        except ValueError as exc:
            raise ValueError("writes are restricted to artifacts/p2_01_system") from exc
        return resolved

    @staticmethod
    def _valid_id(value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ValueError("ID must contain only letters, digits, dot, underscore, or hyphen")
        return value

    def strategies(self) -> dict[str, dict[str, Any]]:
        return STRATEGIES.copy()

    def _catalog(self) -> dict[str, Any]:
        payload = _json(self.catalog_path, {"schema_version": 1, "datasets": {}})
        if not isinstance(payload, dict) or not isinstance(payload.get("datasets"), dict):
            raise ValueError("dataset catalog is invalid")
        return payload

    def datasets(self) -> list[dict[str, Any]]:
        return [
            dict(dataset_id=key, **value)
            for key, value in sorted(self._catalog()["datasets"].items())
        ]

    def historical_data_status(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for name in ("c4_en_v2_100m", "openwebtext_v2_100m"):
            manifest = self.root / "artifacts" / "localmax_v2_data" / name / "data_manifest.json"
            payload = _json(manifest, {})
            paths = payload.get("split_paths", {}) if isinstance(payload, dict) else {}
            declared = [
                self.root / value
                for values in paths.values()
                for value in (values if isinstance(values, list) else [values])
            ]
            present = sum(path.is_file() for path in declared)
            entries.append(
                {
                    "dataset_id": name,
                    "manifest_present": manifest.is_file(),
                    "declared_shards": len(declared),
                    "present_shards": present,
                    "status": (
                        "available"
                        if declared and present == len(declared)
                        else "manifest_only_missing_source_files"
                    ),
                    "declared_tokens": payload.get("actual_gpt2_tokens", 0),
                }
            )
        return entries

    def overview(self) -> dict[str, Any]:
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "unavailable"
        tasks = self.tasks.list()
        return {
            "system_version": SYSTEM_VERSION,
            "datasets": self.datasets(),
            "historical_datasets": self.historical_data_status(),
            "tasks": tasks[:10],
            "completed_tasks": sum(task.get("status") == "completed" for task in tasks),
            "device": device,
            "real_corpus_notice": (
                "历史数据清单存在，原始数据文件缺失，尚不可执行完整真实语料运行。"
            ),
        }

    def inspect_file(self, path: str | Path, *, sample_limit: int = 1000) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if source.suffix not in {".jsonl", ".gz", ".parquet"}:
            raise ValueError("supported formats are JSONL, JSONL.GZ, and Parquet")
        documents = tokens = empty = invalid_text = 0
        fields: Counter[str] = Counter()
        preview: list[dict[str, str]] = []
        for row in iter_records(source):
            documents += 1
            fields.update(row.keys())
            text = row.get("text")
            if not isinstance(text, str):
                invalid_text += 1
                continue
            if not text.strip():
                empty += 1
            tokens += int(row.get("gpt2_tokens") or count_tokens(text))
            if len(preview) < min(sample_limit, 20):
                preview.append(
                    {"id": str(row.get("id", row.get("doc_id", documents))), "text": text[:300]}
                )
        return {
            "path": str(source),
            "sha256": sha256_file(source),
            "documents": documents,
            "estimated_tokens": tokens,
            "empty_text": empty,
            "invalid_text": invalid_text,
            "fields": sorted(fields),
            "preview": preview,
            "sampled_preview_documents": len(preview),
        }

    def import_dataset(
        self, dataset_id: str, path: str | Path, *, source: str = "local", version: str = ""
    ) -> dict[str, Any]:
        dataset_id = self._valid_id(dataset_id)
        inspection = self.inspect_file(path)
        catalog = self._catalog()
        catalog["datasets"][dataset_id] = {
            "path": inspection["path"],
            "source": source,
            "version": version,
            "format": Path(inspection["path"]).suffix,
            "imported_at": _now(),
            **{
                key: inspection[key]
                for key in ("sha256", "documents", "estimated_tokens", "fields")
            },
        }
        self.catalog_path.write_text(
            json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return {"dataset_id": dataset_id, **catalog["datasets"][dataset_id]}

    def dataset(self, dataset_id: str) -> dict[str, Any]:
        dataset_id = self._valid_id(dataset_id)
        try:
            return dict(dataset_id=dataset_id, **self._catalog()["datasets"][dataset_id])
        except KeyError as exc:
            raise KeyError(f"unknown dataset: {dataset_id}") from exc

    def analyze(self, dataset_id: str, *, sample_limit: int = 10000) -> dict[str, Any]:
        if sample_limit < 1:
            raise ValueError("sample_limit must be positive")
        dataset = self.dataset(dataset_id)
        source = Path(dataset["path"])
        lengths: list[int] = []
        tokens: list[int] = []
        issues: Counter[str] = Counter()
        unique: set[str] = set()
        html = urls = 0
        for index, row in enumerate(iter_records(source)):
            if index >= sample_limit:
                break
            text = str(row.get("text", ""))
            normalized = " ".join(text.casefold().split())
            lengths.append(len(text))
            tokens.append(count_tokens(text))
            unique.add(normalized)
            if not text.strip():
                issues["empty"] += 1
            if any(ord(char) < 32 and char not in "\n\r\t" for char in text):
                issues["control_characters"] += 1
            if "\ufffd" in text:
                issues["replacement_character"] += 1
            if "<html" in text.casefold() or "</" in text:
                html += 1
            if "http://" in text.casefold() or "https://" in text.casefold():
                urls += 1
        count = len(lengths)
        report = {
            "dataset_id": dataset_id,
            "analysis_scope": "prefix_sample",
            "sample_documents": count,
            "configured_sample_limit": sample_limit,
            "length": _distribution(lengths),
            "tokens": _distribution(tokens),
            "issues": dict(issues),
            "url_documents": urls,
            "html_like_documents": html,
            "duplicate_rows_in_sample": count - len(unique),
            "language_signal": "script/character heuristic not a high-accuracy language classifier",
            "quality_score": {
                "mean": (sum(1 for size in lengths if size >= 20) / count) if count else 0.0
            },
        }
        report_path = self._inside_output(self.output_root / "analyses" / f"{dataset_id}.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return report

    def save_config(self, name: str, payload: dict[str, Any]) -> Path:
        self._valid_id(name)
        self.validate_filter_config(payload)
        path = self._inside_output(self.output_root / "configs" / f"{name}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def load_config(self, name: str) -> dict[str, Any]:
        self._valid_id(name)
        path = self._inside_output(self.output_root / "configs" / f"{name}.json")
        payload = _json(path, None)
        if not isinstance(payload, dict):
            raise KeyError(f"saved configuration does not exist: {name}")
        self.validate_filter_config(payload)
        return payload

    def preflight(self, *, mode: str = "metadata") -> dict[str, Any]:
        if mode not in {"metadata", "full"}:
            raise ValueError("mode must be metadata or full")
        baseline = (
            self.root
            / "artifacts"
            / "upgrade_reports"
            / "p0-01_preflight"
            / "historical_baseline_sha256.json"
        )
        report = self._inside_output(self.output_root / "preflight" / f"{mode}.json")
        report.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [
                sys.executable,
                str(self.root / "scripts" / "preflight_project.py"),
                "--mode",
                mode,
                "--baseline-manifest",
                str(baseline),
                "--output",
                str(report),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "mode": mode,
            "returncode": completed.returncode,
            "report": str(report),
            "output": completed.stdout,
            "errors": completed.stderr,
        }

    def validate_filter_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        strategy = str(payload.get("strategy", ""))
        self._valid_id(str(payload.get("dataset_id", "")))
        if strategy not in STRATEGIES:
            raise ValueError(f"unknown strategy: {strategy}")
        keep_rate = payload.get("target_keep_rate")
        if keep_rate is not None and not 0 < float(keep_rate) <= 1:
            raise ValueError("target_keep_rate must be in (0, 1]")
        if int(payload.get("max_documents", 100000)) < 1:
            raise ValueError("max_documents must be positive")
        if (
            strategy != "raw"
            and STRATEGIES[strategy].get("proxy")
            and not bool(payload.get("allow_proxy", True))
        ):
            raise ValueError("this strategy is a proxy; set allow_proxy=true to run it")
        return {
            "valid": True,
            "strategy": strategy,
            "streaming": bool(STRATEGIES[strategy].get("streaming")),
            "warning": (
                "Proxy strategy results are labelled as proxy outputs."
                if STRATEGIES[strategy].get("proxy")
                else ""
            ),
        }

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_filter_config(payload)
        task_id = self._valid_id(str(payload.get("task_id") or f"task-{uuid.uuid4().hex[:12]}"))
        task = {
            "task_id": task_id,
            "status": "queued",
            "created_at": _now(),
            "config": payload,
            "output_dir": str(self._inside_output(self.output_root / "runs" / task_id)),
            "error": "",
            "result": {},
        }
        self.tasks.put(task)
        return task

    def start_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.create_task(payload)
        command = [
            sys.executable,
            "-m",
            "quality_system.worker",
            "--root",
            str(self.root),
            "--task-id",
            task["task_id"],
        ]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            command,
            cwd=self.root,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        task["pid"] = process.pid
        task["status"] = "running"
        self.tasks.put(task)
        return task

    def task(self, task_id: str) -> dict[str, Any]:
        return self.tasks.get(self._valid_id(task_id))

    def task_list(self) -> list[dict[str, Any]]:
        return self.tasks.list()

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        task = self.task(task_id)
        if task.get("status") in {"completed", "failed", "cancelled"}:
            return task
        pid = task.get("pid")
        if isinstance(pid, int):
            with suppress(OSError):
                os.kill(pid, 15)
        task["status"] = "cancelled"
        task["error"] = "cancelled by user; completed P1-2 shards remain resumable"
        self.tasks.put(task)
        return task

    def execute_task(self, task_id: str) -> dict[str, Any]:
        task = self.task(task_id)
        task["status"] = "running"
        task["started_at"] = _now()
        self.tasks.put(task)
        started = time.perf_counter()
        log_path = self._inside_output(self.output_root / "logs" / f"{task_id}.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{_now()} started\n", encoding="utf-8")
        try:
            config = task["config"]
            dataset = self.dataset(str(config["dataset_id"]))
            output = self._inside_output(Path(task["output_dir"]))
            output.mkdir(parents=True, exist_ok=True)
            if str(config["strategy"]) == "raw":
                result = run_resumable_pipeline(
                    PipelineConfig(
                        task_id,
                        (str(dataset["path"]),),
                        str(output / "streamed"),
                        batch_size=int(config.get("batch_size", 1000)),
                        config_identity=json.dumps(config, sort_keys=True),
                    ),
                    lambda row: row,
                )
                task["result"] = {
                    "mode": "streaming_raw",
                    "input_docs": result["rows_in"],
                    "kept_docs": result["rows_out"],
                    "manifest": str(output / "streamed" / "pipeline_manifest.json"),
                    "output_dir": str(output / "streamed"),
                    "processed_shards": result["processed_shards"],
                    "skipped_shards": result["skipped_shards"],
                    "rows_per_second": result["rows_per_second"],
                    "peak_tracemalloc_bytes": result["peak_tracemalloc_bytes"],
                }
            else:
                records = list(
                    _limited_records(
                        Path(dataset["path"]), int(config.get("max_documents", 100000))
                    )
                )
                filter_class = get_filter_class(str(config["strategy"]))
                filter_config = FilterConfig(
                    filter_name=str(config["strategy"]),
                    filter_type=getattr(filter_class, "filter_type", str(config["strategy"])),
                    target_keep_rate=config.get("target_keep_rate"),
                    token_budget=config.get("token_budget"),
                    seed=int(config.get("seed", 42)),
                    scope="system",
                    dataset_name=str(config["dataset_id"]),
                    allow_proxy=bool(config.get("allow_proxy", True)),
                    params=dict(config.get("params", {})),
                    notes="P2-1 system run; fixture/sample runs are not real-corpus evidence.",
                )
                instance = filter_class(filter_config)
                outcome = instance.filter(records)
                filter_output = output / "filter"
                instance.write_outputs(filter_output, root=self.root)
                kept = {decision.doc_id for decision in outcome.decisions if decision.keep}
                filtered_data = filter_output / "filtered_data.jsonl"
                with filtered_data.open("w", encoding="utf-8", newline="\n") as handle:
                    for record in records:
                        if record.doc_id in kept:
                            handle.write(
                                json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
                                + "\n"
                            )
                task["result"] = {
                    "mode": "filter",
                    "input_docs": outcome.input_docs,
                    "kept_docs": outcome.kept_docs,
                    "input_tokens": outcome.input_estimated_tokens,
                    "kept_tokens": outcome.kept_estimated_tokens,
                    "document_keep_rate": outcome.document_keep_rate,
                    "token_keep_rate": outcome.token_keep_rate,
                    "manifest": str(filter_output / "filter_manifest.json"),
                    "filtered_dataset": str(filtered_data),
                    "output_dir": str(filter_output),
                }
            task["status"] = "completed"
            task["elapsed_seconds"] = time.perf_counter() - started
            log_path.write_text(
                log_path.read_text(encoding="utf-8") + f"{_now()} completed\n", encoding="utf-8"
            )
        except Exception as exc:
            task["status"] = "failed"
            task["error"] = f"{type(exc).__name__}: {exc}"
            task["elapsed_seconds"] = time.perf_counter() - started
            log_path.write_text(
                log_path.read_text(encoding="utf-8") + f"{_now()} failed: {task['error']}\n",
                encoding="utf-8",
            )
        task["log_path"] = str(log_path)
        self.tasks.put(task)
        return task

    def export_task(self, task_id: str, *, archive_name: str | None = None) -> Path:
        task = self.task(task_id)
        if task.get("status") != "completed":
            raise ValueError("only completed tasks can be exported")
        name = archive_name or f"{task_id}-export"
        self._valid_id(name)
        source = self._inside_output(Path(task["result"]["output_dir"]))
        target = self._inside_output(self.output_root / "exports" / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        return Path(shutil.make_archive(str(target), "zip", root_dir=source))

    def evaluate_smoke_training(
        self, training_manifest_path: str, *, name: str = "lm-smoke"
    ) -> dict[str, Any]:
        """Call the existing Step 7 LM evaluator; never relabel it as main evidence."""
        from evaluation_v2.base import EvaluationConfig
        from evaluation_v2.lm_metrics import run_lm_evaluation

        self._valid_id(name)
        source = Path(training_manifest_path)
        source = source if source.is_absolute() else self.root / source
        if not source.is_file():
            raise FileNotFoundError(f"training manifest does not exist: {source}")
        try:
            relative = source.resolve().relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ValueError("training manifest must be inside the project root") from exc
        config = EvaluationConfig.from_mapping(
            {
                "evaluation_name": name,
                "evaluation_type": "lm",
                "scope": "smoke",
                "method_name": "system_requested",
                "dataset_name": "user_selected",
                "training_manifest_path": relative,
                "smoke_only": True,
                "notes": "P2-1 UI invocation of existing smoke evaluator; not main evidence.",
            }
        )
        output = self._inside_output(self.output_root / "evaluations" / name)
        return run_lm_evaluation(config, output, self.root).to_dict()

    def task_log(self, task_id: str, *, max_bytes: int = 100_000) -> str:
        task = self.task(task_id)
        path = Path(task.get("log_path", ""))
        return path.read_text(encoding="utf-8")[-max_bytes:] if path.is_file() else "未提供"


def _limited_records(path: Path, limit: int) -> Iterator[FilterInput]:
    for index, row in enumerate(iter_records(path)):
        if index >= limit:
            break
        if "doc_id" not in row and "id" in row:
            row = {**row, "doc_id": row["id"]}
        yield FilterInput.from_mapping(row, index)


def _distribution(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "min": 0, "max": 0, "mean": 0.0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "p50": sorted(values)[len(values) // 2],
    }
