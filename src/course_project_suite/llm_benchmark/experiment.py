from __future__ import annotations

import csv
import json
import os
import platform
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, cast

import torch

from .attention import attention_environment, benchmark_attention_suite
from .char_lm import TrainConfig, train_character_lm
from .dataset import (
    CorpusSource,
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
from .quality import filter_by_quality, score_documents
from .reporting import generate_figures
from .research import (
    build_curriculum_report,
    build_downstream_rows,
    build_generation_quality_report,
    build_pipeline_order_report,
    build_privacy_utility_tradeoff_rows,
    build_retention_pareto_rows,
    generation_samples_markdown,
)
from .statistics import aggregate_model_runs, summarize


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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _model_summary(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
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
        variant_summary: dict[str, Any] = {
            metric: summarize([float(run[metric]) for run in variant_runs]) for metric in metrics
        }
        variant_summary["train_characters"] = variant_runs[0]["train_characters"]
        variant_summary["seeds"] = [run["seed"] for run in variant_runs]
        summary[variant] = variant_summary
    return summary


def _write_summary_tables(output: Path, summary: dict[str, dict[str, Any]]) -> None:
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
        "Mode: generated from the benchmark configuration in `results.json`.",
        "Seed setting: see the `Seeds` column.",
        "Training budget: see `results_summary.csv` and `token_budget_report.json`.",
        (
            "Interpretation: compact runs validate reproducibility and "
            "instrumentation; they are not paper-level model-quality conclusions."
        ),
        (
            "Limitation note: larger datasets, longer training, and fixed "
            "method tuning are still required for paper claims."
        ),
        "",
        (
            "| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | "
            "BPC | Next-char accuracy |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['variant']}` | {row['seeds']} | {row['val_loss_mean']:.4f} "
            f"+/- {row['val_loss_std']:.4f} | "
            f"{row['perplexity_mean']:.2f} +/- {row['perplexity_std']:.2f} | "
            f"{row['bits_per_character_mean']:.3f} | {row['next_char_accuracy_mean']:.3f} |"
        )
    (output / "results_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_hdqs_sweep_report(
    documents: list[str],
    *,
    raw_perplexity: float | None = None,
    hdqs_perplexity: float | None = None,
) -> dict[str, Any]:
    thresholds = [0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86]
    threshold_rows = []
    for threshold in thresholds:
        retained, scored = filter_by_quality(documents, threshold=threshold)
        metrics = quality_metrics(retained)
        threshold_rows.append(
            {
                "threshold": threshold,
                "retained_documents": metrics["documents"],
                "retained_characters": metrics["characters"],
                "retention_rate_documents": metrics["documents"] / max(1, len(documents)),
                "mean_hdqs_retained": metrics["mean_hdqs"],
                "pii_like_hits": metrics["email_hits"]
                + metrics["phone_hits"]
                + metrics["id_like_hits"],
                "min_score": min((row.score for row in scored), default=None),
                "max_score": max((row.score for row in scored), default=None),
            }
        )
    top_k_rows = []
    for ratio in [0.25, 0.50, 0.75]:
        retained, _ = filter_by_quality(documents, retention_ratio=ratio)
        metrics = quality_metrics(retained)
        top_k_rows.append(
            {
                "retention_ratio": ratio,
                "retained_documents": metrics["documents"],
                "retained_characters": metrics["characters"],
                "mean_hdqs_retained": metrics["mean_hdqs"],
                "pii_like_hits": metrics["email_hits"]
                + metrics["phone_hits"]
                + metrics["id_like_hits"],
            }
        )

    weight_sweep_rows = []
    weight_configs = [
        {
            "name": "balanced_default",
            "weights": {},
            "status": "configured_default",
        },
        {
            "name": "privacy_heavy",
            "weights": {"pii_density_penalty": 2.0, "url_html_noise_penalty": 1.4},
            "status": "requires_model_validation",
        },
        {
            "name": "anti_repetition_heavy",
            "weights": {"repetition_penalty": 2.0, "ngram_repetition_penalty": 1.6},
            "status": "requires_model_validation",
        },
        {
            "name": "diversity_heavy",
            "weights": {"lexical_diversity": 1.8, "token_entropy": 1.4},
            "status": "requires_model_validation",
        },
    ]
    for config in weight_configs:
        weight_sweep_rows.append(
            {
                "config_name": config["name"],
                "weights": config["weights"],
                "status": config["status"],
                "selection_metric": "retention_and_quality_proxy_only",
            }
        )

    status = "not_evaluated_with_model"
    if raw_perplexity is not None and hdqs_perplexity is not None:
        status = (
            "standalone_hdqs_better_in_this_quick_run"
            if hdqs_perplexity < raw_perplexity
            else "standalone_hdqs_not_better_than_raw_in_this_quick_run"
        )

    def _threshold_objective(row: dict[str, Any]) -> float:
        return (
            float(cast(float, row["mean_hdqs_retained"]))
            * float(cast(float, row["retention_rate_documents"]))
            - 0.02 * float(cast(int, row["pii_like_hits"]))
        )

    best_threshold = max(threshold_rows, key=_threshold_objective)
    return {
        "type": "deterministic_hdqs_threshold_and_top_k_sweep",
        "method_name": "HDQS++ / DQCS prototype",
        "threshold_rows": threshold_rows,
        "top_k_rows": top_k_rows,
        "weight_sweep_rows": weight_sweep_rows,
        "best_config": {
            "name": "proxy_best_threshold_from_quick_diagnostics",
            "threshold": best_threshold["threshold"],
            "selection_objective": (
                "mean_hdqs_retained * document_retention_rate - 0.02 * pii_like_hits"
            ),
            "status": "diagnostic_proxy_not_model_validated",
            "reason": (
                "Quick mode does not tune weights on a held-out development split. "
                "This config is a reproducible diagnostic selection, not a "
                "performance claim."
            ),
        },
        "raw_noisy_baseline_perplexity": raw_perplexity,
        "hdqs_filter_perplexity": hdqs_perplexity,
        "standalone_hdqs_status": status,
        "interpretation": (
            "In quick mode, HDQS should be interpreted as a transparent pipeline component. "
            "Standalone HDQS filtering is not treated as a consistently "
            "performance-improving method "
            "until multi-seed and multi-dataset experiments verify that behavior."
        ),
    }


def _write_hdqs_sweep_table(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# HDQS++ Sweep Table",
        "",
        "Mode: generated from the benchmark configuration in `results.json`.",
        "Seed setting: not a model-training table; see sibling `results.json`.",
        "Training budget: data-selection diagnostic; see `token_budget_report.json`.",
        (
            "Interpretation: threshold and top-k rows evaluate deterministic "
            "data-selection behavior."
        ),
        (
            "Limitation note: this table does not prove HDQS++ improves model "
            "quality without larger training runs."
        ),
        "",
        "Threshold and top-k rows are deterministic data-selection diagnostics.",
        "",
        "| Type | Setting | Retained docs | Retained chars | Mean HDQS | PII-like hits |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in report["threshold_rows"]:
        lines.append(
            f"| threshold | {row['threshold']} | {row['retained_documents']} | "
            f"{row['retained_characters']} | {row['mean_hdqs_retained']:.3f} | "
            f"{row['pii_like_hits']} |"
        )
    for row in report["top_k_rows"]:
        lines.append(
            f"| top-k | {row['retention_ratio']} | {row['retained_documents']} | "
            f"{row['retained_characters']} | {row['mean_hdqs_retained']:.3f} | "
            f"{row['pii_like_hits']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_hdqs_failure_cases(path: Path, payload: dict[str, Any]) -> None:
    rows = sorted(
        payload["quality_scores"],
        key=lambda row: (
            float(row["score"]),
            float(row.get("pii_density_penalty", 1.0)),
            float(row.get("url_html_noise_penalty", 1.0)),
        ),
    )[:8]
    lines = [
        "# HDQS++ Failure Cases",
        "",
        "These are score-component diagnostics, not human labels.",
        "",
        "| Document index | Score | PII penalty | URL/HTML penalty | Repetition penalty |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['document_index']} | {float(row['score']):.4f} | "
            f"{float(row.get('pii_density_penalty', 0.0)):.4f} | "
            f"{float(row.get('url_html_noise_penalty', 0.0)):.4f} | "
            f"{float(row.get('repetition_penalty', 0.0)):.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_report(path: Path, payload: dict[str, Any]) -> None:
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
        (
            "This report is generated from a reproducible local experiment. It is evidence "
            "for a paper prototype, not a paper acceptance or institutional-coursework claim."
        ),
        "",
        "## Research Question",
        "",
        (
            "How do deterministic data-quality interventions affect equal-budget "
            "small-scale language-model pretraining under a controlled corruption stress test?"
        ),
        "",
        "## Data Processing",
        "",
        f"- Raw noisy documents: `{raw['documents']}`",
        f"- Full-pipeline retained documents: `{full['documents']}`",
        f"- Raw PII-like hits: `{raw['email_hits'] + raw['phone_hits'] + raw['id_like_hits']}`",
        (
            f"- Full-pipeline PII-like hits: "
            f"`{full['email_hits'] + full['phone_hits'] + full['id_like_hits']}`"
        ),
        f"- Equal character budget: `{payload['token_budget_report']['equal_budget_enabled']}`",
        "",
        "## Model Summary",
        "",
        (
            "| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | "
            "Next-char accuracy |"
        ),
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for name, metrics in summary.items():
        lines.append(
            f"| `{name}` | {','.join(str(seed) for seed in metrics['seeds'])} | "
            f"{metrics['final_val_loss']['mean']:.4f} +/- {metrics['final_val_loss']['std']:.4f} | "
            f"{metrics['final_val_perplexity']['mean']:.2f} +/- "
            f"{metrics['final_val_perplexity']['std']:.2f} | "
            f"{metrics['final_val_next_char_accuracy']['mean']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Auxiliary Attention Benchmark",
            "",
            (
                "The attention measurements compare readable references with PyTorch SDPA. "
                "They are hardware-dependent systems measurements and not a novel "
                "attention-algorithm claim. CPU working-set values are estimates."
            ),
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
            (
                "- Standalone HDQS filtering is reported separately from the full pipeline; "
                "quick-mode artifacts do not support a claim that HDQS alone consistently "
                "improves model quality."
            ),
            (
                "- Full multi-seed experiments remain necessary before making paper-level "
                "empirical claims."
            ),
            (
                "- Tiny Shakespeare and injected corruption are controlled debugging "
                "instruments, not a production web-corpus evaluation."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _environment() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
        "torch_num_threads": torch.get_num_threads(),
    }


def _portable_configuration(config: BenchmarkConfig) -> dict[str, Any]:
    payload = asdict(config)
    for name in ("data_path", "output_dir"):
        path = Path(str(payload[name]))
        try:
            payload[name] = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            payload[name] = path.name
    payload["train_config"] = asdict(config.train_config)
    return payload


def run_benchmark_from_text(
    corpus: str, source: CorpusSource, config: BenchmarkConfig
) -> dict[str, Any]:
    started = time.perf_counter()
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "1")))
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
            "note": (
                "Unequal retention tradeoff mode; do not interpret this as a strict "
                "equal-budget comparison."
            ),
        }
    shared_vocab = "".join(lm_inputs.values()) + validation_text
    model_runs: list[dict[str, Any]] = []
    for variant, train_text in lm_inputs.items():
        for seed in config.seeds:
            train_config = replace(
                config.train_config, device=config.device, seed=seed, checkpoint_path=None
            )
            metrics = train_character_lm(train_text, validation_text, shared_vocab, train_config)
            model_runs.append({"variant": variant, "seed": seed, **metrics})
    summary = _model_summary(model_runs)
    hdqs_sweep_report = _build_hdqs_sweep_report(
        noisy_documents,
        raw_perplexity=summary.get("raw_noisy_baseline", {})
        .get("final_val_perplexity", {})
        .get("mean"),
        hdqs_perplexity=summary.get("hdqs_filter", {}).get("final_val_perplexity", {}).get("mean"),
    )
    attention = benchmark_attention_suite(
        config.attention_lengths,
        repeats=config.attention_repeats,
        device=config.device,
    )
    full_documents = variants["full_pipeline"]
    canary_report = evaluate_synthetic_canaries(
        noisy_documents,
        full_documents,
        cast(list[dict[str, str]], noise_result.report["synthetic_pii_canaries"]),
    )
    privacy_report = {
        **canary_report,
        "raw_pii_hits": pii_hit_count(noisy_documents),
        "full_pipeline_pii_hits": pii_hit_count(full_documents),
    }
    downstream_report: dict[str, Any] = {
        variant: {
            "task": "held-out next-character prediction",
            "next_char_accuracy": metrics["final_val_next_char_accuracy"],
        }
        for variant, metrics in summary.items()
    }
    downstream_rows = build_downstream_rows(summary)
    downstream_report["rows"] = downstream_rows
    generation_quality_report = build_generation_quality_report(model_runs)
    curriculum_report = build_curriculum_report(noisy_documents)
    pipeline_order_report = build_pipeline_order_report(noisy_documents)
    retention_pareto_rows = build_retention_pareto_rows(variant_metrics, summary)
    privacy_utility_rows = build_privacy_utility_tradeoff_rows(variant_metrics, summary)
    seed_rows, aggregate_rows, statistical_tests = aggregate_model_runs(model_runs)
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
        "hdqs_sweep_report": hdqs_sweep_report,
        "curriculum_report": curriculum_report,
        "pipeline_order_report": pipeline_order_report,
        "retention_pareto": retention_pareto_rows,
        "privacy_utility_tradeoff": privacy_utility_rows,
        "downstream_report": downstream_report,
        "generation_quality_report": generation_quality_report,
        "privacy_report": privacy_report,
        "statistical_tests": statistical_tests,
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
    _write_json(output / "hdqs_sweep_report.json", hdqs_sweep_report)
    _write_hdqs_sweep_table(output / "hdqs_sweep_table.md", hdqs_sweep_report)
    _write_json(output / "hdqs_best_config.json", hdqs_sweep_report["best_config"])
    _write_json(output / "curriculum_report.json", curriculum_report)
    _write_json(output / "pipeline_order_report.json", pipeline_order_report)
    _write_csv(output / "retention_pareto.csv", retention_pareto_rows)
    _write_csv(output / "privacy_utility_tradeoff.csv", privacy_utility_rows)
    _write_json(output / "privacy_report.json", privacy_report)
    _write_json(output / "canary_memorization_report.json", privacy_report)
    _write_json(output / "downstream_report.json", downstream_report)
    _write_csv(output / "downstream_results.csv", downstream_rows)
    _write_json(output / "generation_quality_report.json", generation_quality_report)
    (output / "generation_samples.md").write_text(
        generation_samples_markdown(model_runs), encoding="utf-8"
    )
    _write_csv(output / "seed_level_results.csv", seed_rows)
    _write_csv(output / "aggregated_results.csv", aggregate_rows)
    _write_json(output / "statistical_tests.json", statistical_tests)
    _write_json(output / "attention_benchmark.json", payload["attention_benchmark"])
    _write_json(output / "duplicate_clusters.json", payload["duplicate_clusters"])
    _write_json(output / "environment.json", payload["environment"])
    _write_csv(output / "quality_scores.csv", quality_scores)
    _write_hdqs_failure_cases(output / "hdqs_failure_cases.md", payload)
    curve_rows = [
        {"variant": run["variant"], "seed": run["seed"], **point}
        for run in model_runs
        for point in run["curve"]
    ]
    _write_csv(output / "training_curves.csv", curve_rows)
    injected_counts = cast(dict[str, int], noise_result.report["injected_counts"])
    noise_rows = [
        {"noise_type": name, "count": count} for name, count in sorted(injected_counts.items())
    ]
    _write_csv(output / "noise_type_breakdown.csv", noise_rows)
    removal_rows = [
        {
            "variant": name,
            "documents": metrics["documents"],
            "duplicate_documents": metrics["duplicate_documents"],
            "pii_like_hits": int(metrics["email_hits"])
            + int(metrics["phone_hits"])
            + int(metrics["id_like_hits"]),
            "mean_hdqs": metrics["mean_hdqs"],
        }
        for name, metrics in variant_metrics.items()
    ]
    _write_csv(output / "noise_removal_effectiveness.csv", removal_rows)
    _write_summary_tables(output, summary)
    generate_figures(payload, output)
    _write_report(output / "REPORT.md", payload)
    return payload


def run_benchmark(config: BenchmarkConfig) -> dict[str, object]:
    corpus, source = load_public_corpus(config.data_path)
    return run_benchmark_from_text(corpus, source, config)
