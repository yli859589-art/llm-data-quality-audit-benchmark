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
    "wikitext2": "configs/datasets/wikitext2.yaml",
    "openwebtext_sample": "configs/datasets/openwebtext_sample.yaml",
    "c4_sample": "configs/datasets/c4_sample.yaml",
    "mixed_debug": "configs/datasets/mixed_debug.yaml",
}


@dataclass(frozen=True)
class DatasetMatrixResult:
    dataset_key: str
    dataset_name: str
    output_dir: str
    used_fallback: bool
    status: str
    raw_perplexity: float | None = None
    full_pipeline_perplexity: float | None = None
    error: str | None = None


def dataset_keys_for_mode(mode: str) -> tuple[str, ...]:
    if mode == "quick":
        return ("tiny_shakespeare", "mixed_debug")
    if mode in {"paper-prototype", "full"}:
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
        train_config = TrainConfig(steps=8, eval_interval=4, eval_batches=2, n_embd=24)
        seeds = (23, 42, 3407)
        max_documents = 80
        train_chars = 22000
        validation_chars = 6000
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


def _write_summary(output_dir: Path, rows: list[DatasetMatrixResult]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_rows = [row.__dict__ for row in rows]
    with (output_dir / "dataset_matrix_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
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
    (output_dir / "dataset_matrix_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    for dataset_key in dataset_keys:
        config_path = resolve_dataset_config(dataset_key, root)
        try:
            dataset = load_configured_dataset(config_path, root=root, allow_network=allow_network)
            benchmark_config = benchmark_config_for_dataset(
                dataset, dataset_key=dataset_key, mode=mode, output_dir=output_dir
            )
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
                    "note": (
                        "Dataset matrix dry-run card. It validates loading, fallback, "
                        "source attribution, and output routing without training a model."
                    ),
                }
                (dataset_output / "dataset_card.json").write_text(
                    json.dumps(dry_run_card, indent=2), encoding="utf-8"
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
            payload = run_benchmark_from_text(dataset.text, dataset.source, benchmark_config)
            summary: dict[str, dict[str, Any]] = payload["model_summary"]
            rows.append(
                DatasetMatrixResult(
                    dataset_key=dataset_key,
                    dataset_name=dataset.source.dataset_name,
                    output_dir=_portable_path(benchmark_config.output_dir, root),
                    used_fallback=dataset.used_fallback,
                    status="ok",
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
