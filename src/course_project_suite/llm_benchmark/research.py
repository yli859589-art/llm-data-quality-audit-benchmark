from __future__ import annotations

import random
from typing import Any

from course_project_suite.cs336.data import clean_common_crawl_text, redact_pii

from .dedup import exact_deduplicate
from .near_dedup import near_deduplicate
from .privacy import pii_hit_count
from .quality import ID_RE, filter_by_quality, score_documents


def _quality_metrics(documents: list[str]) -> dict[str, float | int]:
    from .dataset import quality_metrics

    return quality_metrics(documents)


def build_curriculum_report(
    documents: list[str],
    *,
    seed: int = 23,
    retention_ratio: float = 0.75,
) -> dict[str, Any]:
    scored = score_documents(documents)
    score_by_index = {row.index: row.score for row in scored}
    ranked_high = [row.index for row in sorted(scored, key=lambda row: row.score, reverse=True)]
    ranked_low = list(reversed(ranked_high))
    rng = random.Random(seed)
    random_order = list(range(len(documents)))
    rng.shuffle(random_order)

    def stratified() -> list[int]:
        high = ranked_high[: len(ranked_high) // 2]
        low = ranked_low[: len(ranked_low) - len(high)]
        output: list[int] = []
        for left, right in zip(high, low, strict=False):
            output.extend([left, right])
        output.extend(high[len(low) :])
        output.extend(low[len(high) :])
        return output

    orders = {
        "random_baseline": random_order,
        "high_quality_first": ranked_high,
        "low_quality_first": ranked_low,
        "easy_to_hard": ranked_high,
        "hard_to_easy": ranked_low,
        "quality_stratified_sampling": stratified(),
        "mixed_quality_curriculum": stratified()[::-1],
    }
    keep = max(1, round(len(documents) * retention_ratio))
    strategies = []
    for name, order in orders.items():
        selected = order[:keep]
        selected_scores = [score_by_index[index] for index in selected]
        strategies.append(
            {
                "strategy": name,
                "seed": seed,
                "retention_ratio": retention_ratio,
                "selected_documents": len(selected),
                "selected_indices": selected[:20],
                "mean_selected_hdqs": sum(selected_scores) / max(1, len(selected_scores)),
                "first_five_scores": selected_scores[:5],
                "status": "deterministic_selection_only_not_a_model_result",
            }
        )
    return {
        "method": "DQCS: Data Quality Curriculum Selection",
        "strategies": strategies,
        "limitations": (
            "This quick artifact validates deterministic curriculum construction. "
            "Model-quality effects require multi-seed training runs."
        ),
    }


def _clean(documents: list[str]) -> list[str]:
    return [clean_common_crawl_text(document) for document in documents]


def _redact(documents: list[str]) -> list[str]:
    redacted = [redact_pii(document) for document in documents]
    return [ID_RE.sub("<ID>", document) for document in redacted]


def _exact(documents: list[str]) -> list[str]:
    return exact_deduplicate(documents).documents


def _near(documents: list[str]) -> list[str]:
    return near_deduplicate(documents).documents


def _hdqs(documents: list[str]) -> list[str]:
    return filter_by_quality(documents, threshold=0.80)[0]


PIPELINE_STEPS = {
    "clean": _clean,
    "redact": _redact,
    "exact_dedup": _exact,
    "near_dedup": _near,
    "hdqs": _hdqs,
}


def build_pipeline_order_report(documents: list[str]) -> dict[str, Any]:
    orders = {
        "clean_redact_exact_near_hdqs": ("clean", "redact", "exact_dedup", "near_dedup", "hdqs"),
        "clean_dedup_redact_hdqs": ("clean", "exact_dedup", "near_dedup", "redact", "hdqs"),
        "hdqs_clean_dedup": ("hdqs", "clean", "exact_dedup", "near_dedup"),
        "redact_before_dedup": ("redact", "exact_dedup", "near_dedup", "hdqs"),
        "redact_after_dedup": ("exact_dedup", "near_dedup", "redact", "hdqs"),
        "near_dedup_before_hdqs": ("clean", "redact", "near_dedup", "hdqs"),
        "near_dedup_after_hdqs": ("clean", "redact", "hdqs", "near_dedup"),
    }
    rows = []
    for name, steps in orders.items():
        output = list(documents)
        for step in steps:
            output = PIPELINE_STEPS[step](output)
        metrics = _quality_metrics(output)
        rows.append(
            {
                "pipeline_order": name,
                "steps": " -> ".join(steps),
                "retained_documents": metrics["documents"],
                "retained_characters": metrics["characters"],
                "retention_rate_documents": metrics["documents"] / max(1, len(documents)),
                "pii_like_hits": pii_hit_count(output),
                "mean_hdqs": metrics["mean_hdqs"],
            }
        )
    return {
        "type": "pipeline_order_study",
        "rows": rows,
        "limitations": (
            "Rows describe deterministic preprocessing outcomes. They are not "
            "separate trained-model results unless an experiment mode explicitly trains them."
        ),
    }


def build_retention_pareto_rows(
    variants: dict[str, dict[str, float | int]],
    summary: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_chars = float(variants["raw_noisy_baseline"]["characters"])
    rows = []
    for name, metrics in variants.items():
        model_metrics = summary.get(name)
        rows.append(
            {
                "variant": name,
                "retention_ratio": float(metrics["characters"]) / max(1.0, raw_chars),
                "retained_documents": metrics["documents"],
                "mean_hdqs": metrics["mean_hdqs"],
                "pii_like_hits": int(metrics["email_hits"])
                + int(metrics["phone_hits"])
                + int(metrics["id_like_hits"]),
                "perplexity_mean": (
                    model_metrics["final_val_perplexity"]["mean"] if model_metrics else None
                ),
                "status": "trained" if model_metrics else "data_only",
            }
        )
    return rows


def build_privacy_utility_tradeoff_rows(
    variants: dict[str, dict[str, float | int]],
    summary: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for name, metrics in variants.items():
        model_metrics = summary.get(name)
        pii_hits = (
            int(metrics["email_hits"])
            + int(metrics["phone_hits"])
            + int(metrics["id_like_hits"])
        )
        rows.append(
            {
                "variant": name,
                "residual_pii_like_hits": pii_hits,
                "mean_hdqs": metrics["mean_hdqs"],
                "next_char_accuracy_mean": (
                    model_metrics["final_val_next_char_accuracy"]["mean"] if model_metrics else None
                ),
                "perplexity_mean": (
                    model_metrics["final_val_perplexity"]["mean"] if model_metrics else None
                ),
                "status": "trained" if model_metrics else "data_only",
            }
        )
    return rows


def build_downstream_rows(summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for variant, metrics in summary.items():
        next_acc = float(metrics["final_val_next_char_accuracy"]["mean"])
        perplexity = float(metrics["final_val_perplexity"]["mean"])
        rows.append(
            {
                "variant": variant,
                "next_character_accuracy": next_acc,
                "held_out_perplexity": perplexity,
                "held_out_bits_per_character": metrics["final_val_bits_per_character"]["mean"],
                "held_out_noisy_robustness_proxy": 1 / max(1.0, perplexity),
                "simple_cloze_proxy_accuracy": next_acc,
                "toy_sentiment_proxy": "not_run_in_quick_mode",
                "small_classification_proxy": "not_run_in_quick_mode",
                "status": "quick_trained_metric",
            }
        )
    return rows


def build_generation_quality_report(model_runs: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for run in model_runs:
        sample = str(run.get("sample_generation", ""))
        tokens = sample.split()
        repeated = 0
        if len(tokens) >= 3:
            trigrams = list(zip(tokens, tokens[1:], tokens[2:], strict=False))
            repeated = len(trigrams) - len(set(trigrams))
        rows.append(
            {
                "variant": run["variant"],
                "seed": run["seed"],
                "sample_characters": len(sample),
                "generation_repeated_trigrams": repeated,
                "generation_repetition_rate": repeated / max(1, len(tokens) - 2),
                "note": "Small model output; not human preference evaluation.",
            }
        )
    return {"rows": rows}


def generation_samples_markdown(model_runs: list[dict[str, Any]]) -> str:
    lines = [
        "# Small Model Generation Samples",
        "",
        "These samples are produced by compact quick-mode models and are not human-rated.",
        "",
    ]
    for run in model_runs:
        lines.extend(
            [
                f"## {run['variant']} seed={run['seed']}",
                "",
                "Prompt:",
                "",
                "```text",
                str(run.get("sample_prompt", ""))[:240],
                "```",
                "",
                "Generation:",
                "",
                "```text",
                str(run.get("sample_generation", ""))[:500],
                "```",
                "",
            ]
        )
    return "\n".join(lines)
