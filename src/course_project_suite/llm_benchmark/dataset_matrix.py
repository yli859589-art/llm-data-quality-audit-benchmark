from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .char_lm import TrainConfig
from .datasets import ConfiguredDataset, load_configured_dataset
from .experiment import BenchmarkConfig, run_benchmark_from_text

DATASET_CONFIGS = {
    "tiny_shakespeare": "configs/datasets/tiny_shakespeare.yaml",
    "mixed_debug": "configs/datasets/mixed_debug.yaml",
    "synthetic_web_noise": "configs/datasets/synthetic_web_noise.yaml",
    "local_wikitext_sample": "configs/datasets/local_wikitext_sample.yaml",
    "wikitext2": "configs/datasets/wikitext2.yaml",
    "openwebtext_sample": "configs/datasets/openwebtext_sample.yaml",
    "c4_sample": "configs/datasets/c4_sample.yaml",
}

OPTIONAL_REMOTE_DATASETS = {"wikitext2", "openwebtext_sample", "c4_sample"}
PAPER_PROTOTYPE_TRAINED_DATASETS = (
    "tiny_shakespeare",
    "mixed_debug",
    "synthetic_web_noise",
    "local_wikitext_sample",
)


@dataclass(frozen=True)
class DatasetMatrixResult:
    dataset_key: str
    dataset_name: str
    output_dir: str
    used_fallback: bool
    status: str
    raw_perplexity: float | None = None
    full_pipeline_perplexity: float | None = None
    fallback_reason: str | None = None
    error: str | None = None


def dataset_keys_for_mode(mode: str) -> tuple[str, ...]:
    if mode == "quick":
        return ("tiny_shakespeare", "mixed_debug")
    if mode == "paper-prototype":
        return PAPER_PROTOTYPE_TRAINED_DATASETS + tuple(OPTIONAL_REMOTE_DATASETS)
    if mode == "full":
        return tuple(DATASET_CONFIGS)
    raise ValueError("mode must be 'quick', 'paper-prototype', or 'full'.")


def resolve_dataset_config(dataset_key: str, root: Path) -> Path:
    try:
        relative = DATASET_CONFIGS[dataset_key]
    except KeyError as error:
        raise ValueError(f"Unknown dataset key: {dataset_key}") from error
    return root / relative


def benchmark_config_for_dataset(
    dataset: ConfiguredDataset,
    *,
    dataset_key: str,
    mode: str,
    output_dir: Path,
) -> BenchmarkConfig:
    if mode == "quick":
        train_config = TrainConfig(steps=8, eval_interval=4, eval_batches=2, n_embd=24)
        seeds: tuple[int, ...] = (23,)
        max_documents = 60
        train_chars = 18000
        validation_chars = 5000
        attention_lengths: tuple[int, ...] = (32, 64)
    elif mode == "paper-prototype":
        train_config = TrainConfig(
            steps=6,
            eval_interval=3,
            eval_batches=1,
            n_embd=24,
            batch_size=4,
            block_size=32,
        )
        seeds = (23,)
        max_documents = 28
        train_chars = 5200
        validation_chars = 1200
        attention_lengths = (32, 64)
    elif mode == "full":
        train_config = TrainConfig()
        seeds = (23, 42, 3407)
        max_documents = 140
        train_chars = 52000
        validation_chars = 9000
        attention_lengths = (32, 64, 128)
    else:
        raise ValueError("mode must be 'quick', 'paper-prototype', or 'full'.")

    return BenchmarkConfig(
        data_path=dataset.source.path,
        output_dir=str(output_dir / dataset_key),
        mode=f"dataset_matrix_{mode}",
        max_documents=max_documents,
        train_chars=train_chars,
        validation_chars=validation_chars,
        train_config=train_config,
        seeds=seeds,
        attention_lengths=attention_lengths,
        attention_repeats=3 if mode in {"quick", "paper-prototype"} else 6,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_fallback_report(
    path: Path,
    *,
    dataset_key: str,
    dataset: ConfiguredDataset,
    command: str,
    reason: str | None,
    status: str,
) -> None:
    _write_json(
        path,
        {
            "dataset_key": dataset_key,
            "dataset_name": dataset.source.dataset_name,
            "used_fallback": dataset.used_fallback,
            "status": status,
            "fallback_reason": reason,
            "command": command,
            "source": dataset.source.source,
            "license_note": dataset.source.license_or_usage_note,
            "note": (
                "Remote optional datasets are not treated as real multi-dataset "
                "evidence unless local data or explicit network access is available."
            ),
        },
    )


def _write_summary(output_dir: Path, rows: list[DatasetMatrixResult]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_rows = [row.__dict__ for row in rows]
    summary_names = ["dataset_matrix_summary"]
    if any(row.status in {"paper_prototype_small_run", "fallback_recorded"} for row in rows):
        summary_names.append("paper_prototype_summary")
    for name in summary_names:
        with (output_dir / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
            writer.writeheader()
            writer.writerows(csv_rows)

    lines = [
        "# Dataset Matrix Summary",
        "",
        (
            "| Dataset key | Loaded dataset | Fallback | Status | "
            "Raw perplexity | Full pipeline perplexity |"
        ),
        "| --- | --- | ---: | --- | ---: | ---: |",
    ]
    for row in rows:
        raw_perplexity = row.raw_perplexity if row.raw_perplexity is not None else "N/A"
        full_perplexity = (
            row.full_pipeline_perplexity if row.full_pipeline_perplexity is not None else "N/A"
        )
        lines.append(
            f"| `{row.dataset_key}` | `{row.dataset_name}` | {row.used_fallback} | {row.status} | "
            f"{raw_perplexity} | {full_perplexity} |"
        )
    for name in summary_names:
        title = "# Dataset Matrix Summary"
        if name == "paper_prototype_summary":
            title = "# Paper-Prototype Dataset Matrix Summary"
        (output_dir / f"{name}.md").write_text(
            "\n".join([title, *lines[1:]]) + "\n", encoding="utf-8"
        )


def _portable_path(path: str | Path, root: Path) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def run_dataset_matrix(
    *,
    root: Path,
    output_dir: Path,
    dataset_keys: tuple[str, ...],
    mode: str = "quick",
    allow_network: bool = False,
    dry_run: bool = False,
) -> list[DatasetMatrixResult]:
    rows: list[DatasetMatrixResult] = []
    command = f"python scripts/run_dataset_matrix.py --mode {mode}"
    if dry_run:
        command += " --dry-run"
    if allow_network:
        command += " --allow-network"
    for dataset_key in dataset_keys:
        config_path = resolve_dataset_config(dataset_key, root)
        try:
            dataset = load_configured_dataset(config_path, root=root, allow_network=allow_network)
            benchmark_config = benchmark_config_for_dataset(
                dataset, dataset_key=dataset_key, mode=mode, output_dir=output_dir
            )
            dataset_output = output_dir / dataset_key
            dataset_output.mkdir(parents=True, exist_ok=True)
            if dry_run:
                dataset_output = output_dir / dataset_key
                dataset_output.mkdir(parents=True, exist_ok=True)
                for child in dataset_output.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                dry_run_card = {
                    **asdict(dataset.source),
                    "used_fallback": dataset.used_fallback,
                    "dry_run": True,
                    "configuration": dataset.configuration,
                    "command": command,
                    "note": (
                        "Dataset matrix dry-run card. It validates loading, fallback, "
                        "source attribution, and output routing without training a model."
                    ),
                }
                _write_json(dataset_output / "dataset_card.json", dry_run_card)
                _write_fallback_report(
                    dataset_output / "fallback_report.json",
                    dataset_key=dataset_key,
                    dataset=dataset,
                    command=command,
                    reason="dry_run_requested",
                    status="dry_run",
                )
                rows.append(
                    DatasetMatrixResult(
                        dataset_key=dataset_key,
                        dataset_name=dataset.source.dataset_name,
                        output_dir=_portable_path(benchmark_config.output_dir, root),
                        used_fallback=dataset.used_fallback,
                        status="dry_run",
                    )
                )
                continue
            if (
                mode == "paper-prototype"
                and dataset_key in OPTIONAL_REMOTE_DATASETS
                and dataset.used_fallback
            ):
                reason = (
                    "Optional remote dataset was not downloaded. Provide local data or pass "
                    "--allow-network after reviewing the upstream dataset policy."
                )
                fallback_card = {
                    **asdict(dataset.source),
                    "dataset_key": dataset_key,
                    "fallback": True,
                    "fallback_reason": reason,
                    "raw_chars": dataset.source.chars,
                    "retained_chars": None,
                    "retention_rate": None,
                    "num_docs": None,
                    "seed": None,
                    "token_budget": benchmark_config.train_chars,
                    "variants_run": [],
                    "runtime_seconds": 0.0,
                    "command": command,
                    "license_note": dataset.source.license_or_usage_note,
                    "status": "fallback_recorded",
                }
                _write_json(dataset_output / "dataset_card.json", fallback_card)
                _write_json(
                    dataset_output / "results.json",
                    {
                        "mode": "dataset_matrix_paper_prototype",
                        "dataset_key": dataset_key,
                        "status": "fallback_recorded",
                        "used_fallback": True,
                        "fallback_reason": reason,
                        "command": command,
                    },
                )
                _write_fallback_report(
                    dataset_output / "fallback_report.json",
                    dataset_key=dataset_key,
                    dataset=dataset,
                    command=command,
                    reason=reason,
                    status="fallback_recorded",
                )
                rows.append(
                    DatasetMatrixResult(
                        dataset_key=dataset_key,
                        dataset_name=dataset.source.dataset_name,
                        output_dir=_portable_path(benchmark_config.output_dir, root),
                        used_fallback=True,
                        status="fallback_recorded",
                        fallback_reason=reason,
                    )
                )
                continue
            payload = run_benchmark_from_text(dataset.text, dataset.source, benchmark_config)
            summary: dict[str, dict[str, Any]] = payload["model_summary"]
            dataset_card = json.loads((output_dir / dataset_key / "dataset_card.json").read_text())
            dataset_card.update(
                {
                    "dataset_key": dataset_key,
                    "fallback": dataset.used_fallback,
                    "seed": ",".join(str(seed) for seed in benchmark_config.seeds),
                    "token_budget": benchmark_config.train_chars,
                    "variants_run": list(payload["model_summary"]),
                    "runtime_seconds": payload["walltime_seconds"],
                    "command": command,
                    "license_note": dataset.source.license_or_usage_note,
                    "status": (
                        "paper_prototype_small_run"
                        if mode == "paper-prototype"
                        else "ok"
                    ),
                }
            )
            _write_json(output_dir / dataset_key / "dataset_card.json", dataset_card)
            _write_fallback_report(
                output_dir / dataset_key / "fallback_report.json",
                dataset_key=dataset_key,
                dataset=dataset,
                command=command,
                reason=None,
                status="trained",
            )
            rows.append(
                DatasetMatrixResult(
                    dataset_key=dataset_key,
                    dataset_name=dataset.source.dataset_name,
                    output_dir=_portable_path(benchmark_config.output_dir, root),
                    used_fallback=dataset.used_fallback,
                    status=(
                        "paper_prototype_small_run"
                        if mode == "paper-prototype"
                        else "ok"
                    ),
                    raw_perplexity=summary["raw_noisy_baseline"]["final_val_perplexity"]["mean"],
                    full_pipeline_perplexity=summary["full_pipeline"]["final_val_perplexity"][
                        "mean"
                    ],
                )
            )
        except Exception as error:
            rows.append(
                DatasetMatrixResult(
                    dataset_key=dataset_key,
                    dataset_name="unknown",
                    output_dir=_portable_path(output_dir / dataset_key, root),
                    used_fallback=False,
                    status="error",
                    error=str(error),
                )
            )
    _write_summary(output_dir, rows)
    return rows
