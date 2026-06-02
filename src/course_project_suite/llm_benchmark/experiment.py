from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import csv
import json
import os
from pathlib import Path
import platform
import time

import torch

from .attention import attention_environment, benchmark_attention_suite
from .char_lm import TrainConfig, train_character_lm
from .dataset import (
    analyze_removed_documents,
    build_ablation_variants,
    build_dataset_card,
    chunk_documents,
    concatenate_documents,
    enforce_equal_character_budget,
    load_public_corpus,
    quality_metrics,
)
from .dedup import exact_deduplicate, near_deduplicate
from .noise import NoiseConfig, inject_controlled_noise
from .privacy import evaluate_synthetic_canaries, pii_hit_count
from .quality import score_documents
from .reporting import generate_figures
from .statistics import summarize


@dataclass(frozen=True)
class BenchmarkConfig:
    data_path: str
    output_dir: str
    mode: str = "quick"
    max_documents: int = 60
    train_chars: int = 18000
    validation_chars: int = 5000
    train_config: TrainConfig = TrainConfig(steps=8, eval_interval=4, eval_batches=2, n_embd=24)
    seeds: tuple[int, ...] = (23,)
    lm_variants: tuple[str, ...] = (
        "raw_noisy_baseline",
        "rule_filter_only",
        "hdqs_filter",
        "full_pipeline",
    )
    quality_threshold: float = 0.80
    near_duplicate_threshold: float = 0.82
    equal_character_budget: bool = True
    attention_lengths: tuple[int, ...] = (32, 64)
    attention_repeats: int = 3
    device: str = "cpu"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _model_summary(runs: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    summary = {}
    metrics = [
        "final_train_loss",
        "final_val_loss",
        "final_val_perplexity",
        "final_val_bits_per_character",
        "final_val_next_char_accuracy",
        "tokens_per_second",
        "elapsed_seconds",
    ]
    for variant in sorted({str(run["variant"]) for run in runs}):
        variant_runs = [run for run in runs if run["variant"] == variant]
        summary[variant] = {
            metric: summarize([float(run[metric]) for run in variant_runs]) for metric in metrics
        }
        summary[variant]["train_characters"] = variant_runs[0]["train_characters"]
        summary[variant]["seeds"] = [run["seed"] for run in variant_runs]
    return summary


def _write_summary_tables(output: Path, summary: dict[str, dict[str, object]]) -> None:
    rows = []
    for variant, metrics in summary.items():
        rows.append(
            {
                "variant": variant,
                "seeds": ",".join(str(seed) for seed in metrics["seeds"]),
                "train_characters": metrics["train_characters"],
                "val_loss_mean": metrics["final_val_loss"]["mean"],
                "val_loss_std": metrics["final_val_loss"]["std"],
                "perplexity_mean": metrics["final_val_perplexity"]["mean"],
                "perplexity_std": metrics["final_val_perplexity"]["std"],
                "bits_per_character_mean": metrics["final_val_bits_per_character"]["mean"],
                "next_char_accuracy_mean": metrics["final_val_next_char_accuracy"]["mean"],
                "tokens_per_second_mean": metrics["tokens_per_second"]["mean"],
            }
        )
    _write_csv(output / "results_summary.csv", rows)
    lines = [
        "# Model Results Summary",
        "",
        "| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['variant']}` | {row['seeds']} | {row['val_loss_mean']:.4f} +/- {row['val_loss_std']:.4f} | "
            f"{row['perplexity_mean']:.2f} +/- {row['perplexity_std']:.2f} | "
            f"{row['bits_per_character_mean']:.3f} | {row['next_char_accuracy_mean']:.3f} |"
        )
    (output / "results_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_report(path: Path, payload: dict[str, object]) -> None:
    mode = payload["mode"]
    variants = payload["data_quality_ablation"]
    summary = payload["model_summary"]
    full = variants["full_pipeline"]
    raw = variants["raw_noisy_baseline"]
    lines = [
        "# LLM Data Quality Benchmark: Generated Experiment Report",
        "",
        f"Mode: `{mode}`",
        "",
        "This report is generated from a reproducible local experiment. It is evidence for a paper prototype, not a paper acceptance or institutional-coursework claim.",
        "",
        "## Research Question",
        "",
        "How do deterministic data-quality interventions affect equal-budget small-scale language-model pretraining under a controlled corruption stress test?",
        "",
        "## Data Processing",
        "",
        f"- Raw noisy documents: `{raw['documents']}`",
        f"- Full-pipeline retained documents: `{full['documents']}`",
        f"- Raw PII-like hits: `{raw['email_hits'] + raw['phone_hits'] + raw['id_like_hits']}`",
        f"- Full-pipeline PII-like hits: `{full['email_hits'] + full['phone_hits'] + full['id_like_hits']}`",
        f"- Equal character budget: `{payload['token_budget_report']['equal_budget_enabled']}`",
        "",
        "## Model Summary",
        "",
        "| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | Next-char accuracy |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for name, metrics in summary.items():
        lines.append(
            f"| `{name}` | {','.join(str(seed) for seed in metrics['seeds'])} | "
            f"{metrics['final_val_loss']['mean']:.4f} +/- {metrics['final_val_loss']['std']:.4f} | "
            f"{metrics['final_val_perplexity']['mean']:.2f} +/- {metrics['final_val_perplexity']['std']:.2f} | "
            f"{metrics['final_val_next_char_accuracy']['mean']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Auxiliary Attention Benchmark",
            "",
            "The attention measurements compare readable references with PyTorch SDPA. They are hardware-dependent systems measurements and not a novel attention-algorithm claim. CPU working-set values are estimates.",
            "",
            "## Figures",
            "",
            "![Training curves](training_curves.svg)",
            "",
            "![Retention versus perplexity](retention_vs_perplexity.svg)",
            "",
            "![Quality-score distribution](quality_score_distribution.svg)",
            "",
            "![Privacy versus utility](privacy_vs_utility.svg)",
            "",
            "![Attention throughput](attention_throughput.svg)",
            "",
            "## Limits",
            "",
            "- Quick mode uses one seed and a compact CPU budget for smoke-test reproducibility.",
            "- Full multi-seed experiments remain necessary before making paper-level empirical claims.",
            "- Tiny Shakespeare and injected corruption are controlled debugging instruments, not a production web-corpus evaluation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _environment() -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
        "torch_num_threads": torch.get_num_threads(),
    }


def _portable_configuration(config: BenchmarkConfig) -> dict[str, object]:
    payload = asdict(config)
    for name in ("data_path", "output_dir"):
        path = Path(str(payload[name]))
        try:
            payload[name] = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            payload[name] = path.name
    payload["train_config"] = asdict(config.train_config)
    return payload


def run_benchmark(config: BenchmarkConfig) -> dict[str, object]:
    started = time.perf_counter()
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "1")))
    corpus, source = load_public_corpus(config.data_path)
    validation_text = corpus[-config.validation_chars :]
    base_documents = chunk_documents(
        corpus[: -config.validation_chars], max_documents=config.max_documents
    )
    noise_result = inject_controlled_noise(base_documents, NoiseConfig())
    noisy_documents = noise_result.documents
    exact = exact_deduplicate(noisy_documents)
    near = near_deduplicate(exact.documents, threshold=config.near_duplicate_threshold)
    variants = build_ablation_variants(
        noisy_documents,
        quality_threshold=config.quality_threshold,
        near_threshold=config.near_duplicate_threshold,
    )
    variant_metrics = {name: quality_metrics(documents) for name, documents in variants.items()}
    compared = {name: variants[name] for name in config.lm_variants}
    if config.equal_character_budget:
        lm_inputs, budget_report = enforce_equal_character_budget(compared, config.train_chars)
    else:
        lm_inputs = {
            name: concatenate_documents(documents, config.train_chars)
            for name, documents in compared.items()
        }
        budget_report = {
            "equal_budget_enabled": False,
            "requested_characters": config.train_chars,
            "variants": {
                name: {"training_characters": len(text)} for name, text in lm_inputs.items()
            },
            "note": "Unequal retention tradeoff mode; do not interpret this as a strict equal-budget comparison.",
        }
    shared_vocab = "".join(lm_inputs.values()) + validation_text
    model_runs = []
    for variant, train_text in lm_inputs.items():
        for seed in config.seeds:
            train_config = replace(
                config.train_config, device=config.device, seed=seed, checkpoint_path=None
            )
            metrics = train_character_lm(train_text, validation_text, shared_vocab, train_config)
            model_runs.append({"variant": variant, "seed": seed, **metrics})
    summary = _model_summary(model_runs)
    attention = benchmark_attention_suite(
        config.attention_lengths,
        repeats=config.attention_repeats,
        device=config.device,
    )
    full_documents = variants["full_pipeline"]
    canary_report = evaluate_synthetic_canaries(
        noisy_documents,
        full_documents,
        noise_result.report["synthetic_pii_canaries"],
    )
    privacy_report = {
        **canary_report,
        "raw_pii_hits": pii_hit_count(noisy_documents),
        "full_pipeline_pii_hits": pii_hit_count(full_documents),
    }
    downstream_report = {
        variant: {
            "task": "held-out next-character prediction",
            "next_char_accuracy": metrics["final_val_next_char_accuracy"],
        }
        for variant, metrics in summary.items()
    }
    dataset_card = build_dataset_card(
        source,
        raw_documents=noisy_documents,
        retained_documents=full_documents,
        random_seed=NoiseConfig().seed,
        exact_removed=exact.removed,
        near_removed=near.removed,
    )
    quality_scores = [
        {"document_index": row.index, "score": row.score, **row.components}
        for row in score_documents(noisy_documents)
    ]
    payload = {
        "project": "Data Quality Interventions for Small-Scale Language Model Pretraining",
        "mode": config.mode,
        "research_question": (
            "How do deterministic data-quality interventions affect equal-budget "
            "small-scale language-model pretraining?"
        ),
        "configuration": _portable_configuration(config),
        "dataset": asdict(source),
        "dataset_card": dataset_card,
        "noise_report": noise_result.report,
        "token_budget_report": budget_report,
        "data_quality_ablation": variant_metrics,
        "model_runs": model_runs,
        "model_summary": summary,
        "downstream_report": downstream_report,
        "privacy_report": privacy_report,
        "attention_benchmark": {
            "environment": attention_environment(config.device),
            "rows": attention,
        },
        "duplicate_clusters": {
            "exact_duplicate_clusters": exact.clusters,
            "near_duplicate_clusters": near.clusters,
        },
        "quality_scores": quality_scores,
        "error_analysis": analyze_removed_documents(noisy_documents, full_documents),
        "environment": _environment(),
        "walltime_seconds": time.perf_counter() - started,
        "limitations": [
            "Quick mode is a CPU smoke-test experiment.",
            "Tiny Shakespeare is not a production web crawl.",
            "Injected noise is a controlled stress test.",
        ],
    }
    output = Path(config.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "results.json", payload)
    _write_json(output / "dataset_card.json", dataset_card)
    _write_json(output / "noise_report.json", noise_result.report)
    _write_json(output / "token_budget_report.json", budget_report)
    _write_json(output / "privacy_report.json", privacy_report)
    _write_json(output / "downstream_report.json", downstream_report)
    _write_json(output / "attention_benchmark.json", payload["attention_benchmark"])
    _write_json(output / "duplicate_clusters.json", payload["duplicate_clusters"])
    _write_json(output / "environment.json", payload["environment"])
    _write_csv(output / "quality_scores.csv", quality_scores)
    curve_rows = [
        {"variant": run["variant"], "seed": run["seed"], **point}
        for run in model_runs
        for point in run["curve"]
    ]
    _write_csv(output / "training_curves.csv", curve_rows)
    _write_summary_tables(output, summary)
    generate_figures(payload, output)
    _write_report(output / "REPORT.md", payload)
    return payload
