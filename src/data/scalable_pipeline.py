"""Resumable, bounded-memory JSONL/JSONL.GZ corpus processing primitives."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sqlite3
import tempfile
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def iter_records(path: Path) -> Iterator[dict[str, Any]]:
    """Stream JSONL/JSONL.GZ. Parquet is optional and never silently emulated."""
    if path.suffix == ".parquet":
        try:
            import pyarrow.parquet as pq  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Parquet requires the optional pyarrow dependency") from exc
        for batch in pq.ParquetFile(path).iter_batches():
            yield from batch.to_pylist()
        return
    if not path.is_file():
        raise FileNotFoundError(f"input shard does not exist: {path}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[arg-type]
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"JSON record at {path}:{line_number} is not an object")
            yield row


def batched(rows: Iterable[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    if size < 1:
        raise ValueError("batch size must be positive")
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


@dataclass(frozen=True)
class PipelineConfig:
    task_id: str
    input_paths: tuple[str, ...]
    output_dir: str
    batch_size: int = 1000
    version: str = "p1-02.streaming.v1"
    config_identity: str = ""

    def identity(self) -> str:
        payload = {
            "task_id": self.task_id,
            "version": self.version,
            "inputs": list(self.input_paths),
            "input_hashes": [sha256_file(Path(path)) for path in self.input_paths],
            "batch_size": self.batch_size,
            "config_identity": self.config_identity,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class ResumeState:
    def __init__(self, path: Path, config: PipelineConfig) -> None:
        self.path, self.config = path, config
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS task_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS completed_shards (path TEXT PRIMARY KEY, output_path TEXT NOT NULL, input_hash TEXT NOT NULL, output_hash TEXT NOT NULL, rows_in INTEGER NOT NULL, rows_out INTEGER NOT NULL)"
        )
        stored = self._get("config_identity")
        if stored is not None and stored != config.identity():
            raise ValueError("resume blocked: pipeline configuration or input identity changed")
        self._set("config_identity", config.identity())
        self._set("task_id", config.task_id)
        self.connection.commit()

    def _get(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM task_state WHERE key=?", (key,)).fetchone()
        return str(row[0]) if row else None

    def _set(self, key: str, value: str) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO task_state(key,value) VALUES (?,?)", (key, value)
        )

    def completed(self, path: Path) -> bool:
        row = self.connection.execute(
            "SELECT input_hash, output_path, output_hash FROM completed_shards WHERE path=?",
            (str(path),),
        ).fetchone()
        return bool(
            row
            and row[0] == sha256_file(path)
            and Path(row[1]).is_file()
            and sha256_file(Path(row[1])) == row[2]
        )

    def mark_complete(self, path: Path, output: Path, rows_in: int, rows_out: int) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO completed_shards VALUES (?,?,?,?,?,?)",
            (str(path), str(output), sha256_file(path), sha256_file(output), rows_in, rows_out),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


def run_resumable_pipeline(
    config: PipelineConfig,
    transform: Callable[[dict[str, Any]], dict[str, Any] | None],
    *,
    fail_after_shards: int | None = None,
) -> dict[str, Any]:
    """Atomically process each shard, with durable completed-shard state."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state = ResumeState(output_dir / "resume.sqlite", config)
    started = time.perf_counter()
    tracemalloc.start()
    processed = skipped = rows_in = rows_out = 0
    errors: list[dict[str, str]] = []
    failure: Exception | None = None
    try:
        for index, source_name in enumerate(config.input_paths):
            source = Path(source_name)
            if state.completed(source):
                skipped += 1
                continue
            target = output_dir / f"shard-{index:05d}.jsonl"
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=target.name, suffix=".tmp", dir=output_dir
            )
            os.close(descriptor)  # required before replacement on Windows
            temp = Path(temporary_name)
            count_in = count_out = 0
            try:
                with temp.open("w", encoding="utf-8", newline="\n") as handle:
                    for batch in batched(iter_records(source), config.batch_size):
                        for row in batch:
                            count_in += 1
                            result = transform(row)
                            if result is not None:
                                handle.write(
                                    json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
                                )
                                count_out += 1
                os.replace(temp, target)
                state.mark_complete(source, target, count_in, count_out)
                processed += 1
                rows_in += count_in
                rows_out += count_out
                if fail_after_shards is not None and processed >= fail_after_shards:
                    raise RuntimeError("simulated interruption")
            except Exception as exc:
                temp.unlink(missing_ok=True)
                errors.append({"shard": str(source), "error": f"{type(exc).__name__}: {exc}"})
                failure = exc
                break
    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        state.close()
    elapsed = time.perf_counter() - started
    manifest = {
        "pipeline_version": config.version,
        "task_id": config.task_id,
        "config_identity": config.identity(),
        "processed_shards": processed,
        "skipped_shards": skipped,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "elapsed_seconds": elapsed,
        "rows_per_second": rows_in / max(elapsed, 1e-9),
        "peak_tracemalloc_bytes": peak,
        "errors": errors,
        "output_shards": sorted(str(path) for path in output_dir.glob("shard-*.jsonl")),
    }
    (output_dir / "pipeline_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if failure is not None:
        raise failure
    return manifest
