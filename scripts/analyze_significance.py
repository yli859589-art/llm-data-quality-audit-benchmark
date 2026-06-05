from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from experiment_utils import root
from registry_utils import read_registry_jsonl

MIN_EVALUATED_VALIDATION_TOKENS = 50_000
BOOTSTRAP_ITERATIONS = 2_000
RNG_SEED = 1729
OFFICIAL_METHODS = {
    "raw",
    "random_same_keep_rate",
    "length_filter",
    "dedup_only",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v3",
    "calibrated_quality_scorer",
}
METHOD_CANDIDATE_PRIORITY = [
    "hdqspp_v3",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v2",
    "hdqspp",
]


def _float(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key, "")
    if value in {"", None}:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _int(row: dict[str, Any], key: str) -> int:
    value = row.get(key, "")
    if value in {"", None}:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _completed_training_rows() -> list[dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_registry_jsonl():
        if row.get("dataset_key") != "wikitext2_paper":
            continue
        if row.get("dataset_status") not in {"real_nonfallback", "real_local_nonfallback"}:
            continue
        if row.get("dataset_scope") != "official_split":
            continue
        if row.get("model_size") != "small":
            continue
        if row.get("run_status") != "completed_training":
            continue
        if row.get("baseline_name") not in OFFICIAL_METHODS:
            continue
        if _int(row, "train_tokens") < 1_000_000:
            continue
        if _int(row, "evaluated_validation_tokens") < MIN_EVALUATED_VALIDATION_TOKENS:
            continue
        if (
            not row.get("tokenizer_hash")
            or not row.get("vocab_size")
            or not row.get("parameter_count")
        ):
            continue
        metric = _float(row, "final_val_perplexity")
        if metric is None:
            metric = _float(row, "perplexity_or_proxy_perplexity")
        if metric is None:
            continue
        normalized = dict(row)
        normalized["metric_value"] = metric
        latest[(str(row.get("baseline_name")), str(row.get("seed")))] = normalized
    return list(latest.values())


def _ci95(values: list[float], *, rng: random.Random) -> dict[str, float | None]:
    if not values:
        return {"low": None, "high": None}
    if len(values) == 1:
        return {"low": values[0], "high": values[0]}
    draws = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        sample = [values[rng.randrange(len(values))] for _ in values]
        draws.append(mean(sample))
    draws.sort()
    low_index = int(0.025 * (len(draws) - 1))
    high_index = int(0.975 * (len(draws) - 1))
    return {"low": draws[low_index], "high": draws[high_index]}


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _format_float(value: float | None, digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def _comparison_status(
    paired_seeds: list[str],
    ci: dict[str, float | None],
) -> tuple[str, str]:
    if len(paired_seeds) < 3:
        return "insufficient_seeds", "engineering_observation_only"
    if ci["low"] is not None and ci["low"] > 0 and len(paired_seeds) >= 5:
        return "supported_over_reference", "method_supported"
    if ci["low"] is not None and ci["low"] > 0:
        return "positive_preliminary_trend", "preliminary_trend_only_no_significance_claim"
    if ci["high"] is not None and ci["high"] < 0:
        return "negative_preliminary_trend", "preliminary_trend_only_no_significance_claim"
    return "trend_only_ci_crosses_zero", "trend_only_no_significance_claim"


def _method_status_from_comparisons(
    method_comparisons: list[dict[str, Any]],
    available_methods: set[str],
) -> tuple[str, str, str, str]:
    primary = next(
        (candidate for candidate in METHOD_CANDIDATE_PRIORITY if candidate in available_methods),
        "",
    )
    if not primary:
        return "honest_audit_framework", "", "method_unsupported", "No HDQS candidate has completed official rows."
    by_pair = {
        (row.get("candidate"), row.get("reference")): row
        for row in method_comparisons
    }
    raw = by_pair.get((primary, "raw"))
    if not raw:
        return "honest_audit_framework", primary, "method_unsupported", "Primary candidate has no raw comparison."

    def diff(row: dict[str, Any] | None) -> float:
        if not row:
            return 0.0
        value = row.get("mean_difference_reference_minus_candidate")
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    raw_diff = diff(raw)
    raw_low = raw.get("ci95_low")
    raw_n = int(raw.get("n_paired_seeds") or 0)
    prior_improvements = [
        diff(by_pair.get((primary, reference)))
        for reference in ["hdqspp", "hdqspp_v2"]
        if reference != primary
    ]
    if raw_n >= 5 and raw_low is not None and float(raw_low) > 0:
        secondary = "method_supported_over_raw"
        return (
            "honest_audit_framework",
            primary,
            secondary,
            f"Secondary finding `{secondary}`: primary candidate improves over raw with at least 5 paired seeds and CI above zero.",
        )
    if raw_diff > 0:
        secondary = "method_trend_improved_over_raw"
        return (
            "honest_audit_framework",
            primary,
            secondary,
            f"Secondary finding `{secondary}`: primary candidate mean PPL is below raw, but evidence is capped at a trend.",
        )
    if any(value > 0 for value in prior_improvements):
        secondary = "hdqspp_v3_improves_over_v2_trend_but_not_raw"
        return (
            "honest_audit_framework",
            primary,
            secondary,
            f"Secondary finding `{secondary}`: primary candidate improves over an earlier HDQS version but does not beat raw.",
        )
    if raw_diff < 0:
        secondary = "method_unsupported_over_raw"
        return (
            "honest_audit_framework",
            primary,
            secondary,
            f"Secondary finding `{secondary}`: primary candidate underperforms raw in the official paired comparison.",
        )
    return "honest_audit_framework", primary, "method_unsupported", "Primary candidate is tied/unclear versus raw."


def analyze_registry(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RNG_SEED)
    rows = _completed_training_rows()
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_baseline[str(row["baseline_name"])].append(row)

    summaries: list[dict[str, Any]] = []
    bootstrap_ci: dict[str, Any] = {
        "metric": "final_val_perplexity",
        "direction": "lower_is_better",
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "rng_seed": RNG_SEED,
        "mean_confidence_intervals": {},
        "paired_difference_confidence_intervals": {},
    }
    for baseline, baseline_rows in sorted(by_baseline.items()):
        metrics = [float(row["metric_value"]) for row in baseline_rows]
        ci = _ci95(metrics, rng=rng)
        seed_values = sorted(
            {str(row.get("seed", "")) for row in baseline_rows if row.get("seed") != ""}
        )
        source_run_ids = sorted(
            {str(row.get("run_id", "")) for row in baseline_rows if row.get("run_id")}
        )
        summaries.append(
            {
                "dataset_key": "wikitext2_paper",
                "dataset_status": "real_nonfallback",
                "dataset_scope": "official_split",
                "baseline_name": baseline,
                "model_size": "small",
                "seeds": " ".join(seed_values),
                "n_seeds": len(seed_values),
                "metric": "final_val_perplexity",
                "mean": mean(metrics),
                "std": stdev(metrics) if len(metrics) > 1 else 0.0,
                "ci95_low": ci["low"],
                "ci95_high": ci["high"],
                "tokenizer_hash": baseline_rows[0].get("tokenizer_hash", ""),
                "vocab_size": baseline_rows[0].get("vocab_size", ""),
                "parameter_count": baseline_rows[0].get("parameter_count", ""),
                "train_tokens": min(_int(row, "train_tokens") for row in baseline_rows),
                "evaluated_validation_tokens": min(
                    _int(row, "evaluated_validation_tokens") for row in baseline_rows
                ),
                "source_run_ids": " ".join(source_run_ids),
            }
        )
        bootstrap_ci["mean_confidence_intervals"][baseline] = ci

    raw_by_seed = {
        str(row.get("seed")): float(row["metric_value"])
        for row in by_baseline.get("raw", [])
        if row.get("seed") not in {"", None}
    }
    comparisons: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    for baseline, baseline_rows in sorted(by_baseline.items()):
        if baseline == "raw":
            continue
        baseline_by_seed = {
            str(row.get("seed")): float(row["metric_value"])
            for row in baseline_rows
            if row.get("seed") not in {"", None}
        }
        paired_seeds = sorted(
            set(raw_by_seed) & set(baseline_by_seed),
            key=lambda value: int(value),
        )
        diffs = [raw_by_seed[seed] - baseline_by_seed[seed] for seed in paired_seeds]
        ci = _ci95(diffs, rng=rng)
        diff_mean = mean(diffs) if diffs else None
        diff_std = stdev(diffs) if len(diffs) > 1 else None
        effect = (
            diff_mean / diff_std
            if diff_mean is not None and diff_std not in {None, 0.0}
            else None
        )
        if len(paired_seeds) < 3:
            status = "insufficient_seeds"
            safe_claim = "engineering_observation_only"
        elif ci["low"] is not None and ci["low"] > 0:
            status = "positive_preliminary_trend"
            safe_claim = "preliminary_trend_only_no_significance_claim"
        elif ci["high"] is not None and ci["high"] < 0:
            status = "negative_preliminary_trend"
            safe_claim = "preliminary_trend_only_no_significance_claim"
        else:
            status = "trend_only_ci_crosses_zero"
            safe_claim = "trend_only_no_significance_claim"
        comparison = {
            "comparison": f"{baseline}_vs_raw",
            "dataset_key": "wikitext2_paper",
            "model_size": "small",
            "baseline": baseline,
            "reference": "raw",
            "metric": "final_val_perplexity",
            "direction": "positive_diff_means_baseline_lower_perplexity",
            "paired_seeds": " ".join(paired_seeds),
            "n_paired_seeds": len(paired_seeds),
            "mean_difference_raw_minus_baseline": diff_mean,
            "ci95_low": ci["low"],
            "ci95_high": ci["high"],
            "status": status,
            "safe_claim_level": safe_claim,
        }
        comparisons.append(comparison)
        effects.append(
            {
                "comparison": comparison["comparison"],
                "effect_size_raw_minus_baseline_over_paired_std": effect,
                "mean_difference_raw_minus_baseline": diff_mean,
                "paired_std": diff_std,
                "n_paired_seeds": len(paired_seeds),
                "safe_claim_level": safe_claim,
            }
        )
        bootstrap_ci["paired_difference_confidence_intervals"][baseline] = ci

    method_comparisons: list[dict[str, Any]] = []
    candidate_methods = [
        method for method in METHOD_CANDIDATE_PRIORITY if method in by_baseline
    ]
    references = ["raw", "random_same_keep_rate", "dedup_only", "hdqspp", "hdqspp_v2"]
    for candidate in candidate_methods:
        candidate_by_seed = {
            str(row.get("seed")): float(row["metric_value"])
            for row in by_baseline[candidate]
            if row.get("seed") not in {"", None}
        }
        for reference in references:
            if reference == candidate or reference not in by_baseline:
                continue
            reference_by_seed = {
                str(row.get("seed")): float(row["metric_value"])
                for row in by_baseline.get(reference, [])
                if row.get("seed") not in {"", None}
            }
            paired_seeds = sorted(
                set(candidate_by_seed) & set(reference_by_seed),
                key=lambda value: int(value),
            )
            diffs = [
                reference_by_seed[seed] - candidate_by_seed[seed]
                for seed in paired_seeds
            ]
            ci = _ci95(diffs, rng=rng)
            diff_mean = mean(diffs) if diffs else None
            status, safe_claim = _comparison_status(paired_seeds, ci)
            method_comparisons.append(
                {
                    "comparison": f"{candidate}_vs_{reference}",
                    "reference": reference,
                    "candidate": candidate,
                    "paired_seeds": " ".join(paired_seeds),
                    "n_paired_seeds": len(paired_seeds),
                    "mean_difference_reference_minus_candidate": diff_mean,
                    "mean_difference_reference_minus_v2": diff_mean,
                    "ci95_low": ci["low"],
                    "ci95_high": ci["high"],
                    "status": status,
                    "safe_claim_level": safe_claim,
                }
            )
    for candidate, reference in [
        ("random_same_keep_rate", "raw"),
        ("dedup_only", "raw"),
    ]:
        if candidate not in by_baseline or reference not in by_baseline:
            continue
        candidate_by_seed = {
            str(row.get("seed")): float(row["metric_value"])
            for row in by_baseline[candidate]
            if row.get("seed") not in {"", None}
        }
        reference_by_seed = {
            str(row.get("seed")): float(row["metric_value"])
            for row in by_baseline[reference]
            if row.get("seed") not in {"", None}
        }
        paired_seeds = sorted(
            set(candidate_by_seed) & set(reference_by_seed),
            key=lambda value: int(value),
        )
        diffs = [reference_by_seed[seed] - candidate_by_seed[seed] for seed in paired_seeds]
        ci = _ci95(diffs, rng=rng)
        diff_mean = mean(diffs) if diffs else None
        status, safe_claim = _comparison_status(paired_seeds, ci)
        method_comparisons.append(
            {
                "comparison": f"{candidate}_vs_{reference}",
                "reference": reference,
                "candidate": candidate,
                "paired_seeds": " ".join(paired_seeds),
                "n_paired_seeds": len(paired_seeds),
                "mean_difference_reference_minus_candidate": diff_mean,
                "mean_difference_reference_minus_v2": "",
                "ci95_low": ci["low"],
                "ci95_high": ci["high"],
                "status": status,
                "safe_claim_level": safe_claim,
            }
        )

    summary_fields = [
        "dataset_key",
        "dataset_status",
        "dataset_scope",
        "baseline_name",
        "model_size",
        "seeds",
        "n_seeds",
        "metric",
        "mean",
        "std",
        "ci95_low",
        "ci95_high",
        "tokenizer_hash",
        "vocab_size",
        "parameter_count",
        "train_tokens",
        "evaluated_validation_tokens",
        "source_run_ids",
    ]
    comparison_fields = [
        "comparison",
        "dataset_key",
        "model_size",
        "baseline",
        "reference",
        "metric",
        "direction",
        "paired_seeds",
        "n_paired_seeds",
        "mean_difference_raw_minus_baseline",
        "ci95_low",
        "ci95_high",
        "status",
        "safe_claim_level",
    ]
    effect_fields = [
        "comparison",
        "effect_size_raw_minus_baseline_over_paired_std",
        "mean_difference_raw_minus_baseline",
        "paired_std",
        "n_paired_seeds",
        "safe_claim_level",
    ]
    method_fields = [
        "comparison",
        "reference",
        "candidate",
        "paired_seeds",
        "n_paired_seeds",
        "mean_difference_reference_minus_candidate",
        "mean_difference_reference_minus_v2",
        "ci95_low",
        "ci95_high",
        "status",
        "safe_claim_level",
    ]

    _write_csv(output_dir / "main_results.csv", summaries, summary_fields)
    _write_csv(output_dir / "significance_tests.csv", comparisons, comparison_fields)
    _write_csv(output_dir / "effect_sizes.csv", effects, effect_fields)
    _write_csv(output_dir / "method_comparison_summary.csv", method_comparisons, method_fields)
    (output_dir / "bootstrap_ci.json").write_text(
        json.dumps(bootstrap_ci, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "significance_tests.json").write_text(
        json.dumps(
            {
                "metric": "final_val_perplexity",
                "direction": "lower_is_better",
                "tests": comparisons,
                "comparisons": comparisons,
                "method_comparisons": method_comparisons,
                "safe_claim_rule": "With only 3 seeds, results are capped at preliminary trend.",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (output_dir / "main_results.tex").write_text(
        "% Auto-generated lightweight LaTeX table.\n"
        "\\begin{tabular}{lrrrr}\n"
        "Baseline & Seeds & Mean PPL & CI Low & CI High\\\\\n"
        "\\hline\n"
        + "\n".join(
            f"{row['baseline_name']} & {row['n_seeds']} & "
            f"{_format_float(row['mean'])} & {_format_float(row['ci95_low'])} & "
            f"{_format_float(row['ci95_high'])}\\\\"
            for row in summaries
        )
        + "\n\\end{tabular}\n",
        encoding="utf-8",
    )
    report_lines = [
        "# Claim Safety Report",
        "",
        "Dataset: WikiText-2 official dev split, real non-fallback local copy.",
        "Metric: final validation perplexity from completed small-model training runs.",
        "",
        "Rule: because this phase uses only 3 seeds, every model-quality claim is "
        "capped at preliminary trend. No statistically supported claim is made.",
        "",
        "## Paired Comparisons",
        "",
    ]
    if not comparisons:
        report_lines.append("- No paired comparisons available.")
    for row in comparisons:
        report_lines.append(
            "- "
            f"`{row['comparison']}`: mean raw-minus-baseline diff "
            f"{_format_float(row['mean_difference_raw_minus_baseline'])}, "
            f"95% bootstrap CI [{_format_float(row['ci95_low'])}, "
            f"{_format_float(row['ci95_high'])}], "
            f"status `{row['status']}`, safe claim `{row['safe_claim_level']}`."
        )
    (output_dir / "claim_safety_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    method_status, primary_candidate, secondary_method_finding, method_reason = _method_status_from_comparisons(
        method_comparisons,
        set(by_baseline),
    )
    status_lines = [
        "# Method Status Report",
        "",
        f"- Method status: `{method_status}`",
        f"- Secondary method finding: `{secondary_method_finding}`",
        f"- Primary candidate: `{primary_candidate or 'none'}`",
        f"- Reason: {method_reason}",
        "- CCF-C ready: `false`",
        "",
        "## Method Comparisons",
        "",
        "| Comparison | Mean reference-minus-candidate | CI | Status | Safe claim |",
        "|---|---:|---|---|---|",
    ]
    for row in method_comparisons:
        status_lines.append(
            f"| `{row['comparison']}` | "
            f"{_format_float(row.get('mean_difference_reference_minus_candidate'))} | "
            f"[{_format_float(row.get('ci95_low'))}, {_format_float(row.get('ci95_high'))}] | "
            f"`{row['status']}` | `{row['safe_claim_level']}` |"
        )
    (output_dir / "method_status_report.md").write_text(
        "\n".join(status_lines) + "\n",
        encoding="utf-8",
    )
    return {
        "summaries": summaries,
        "comparisons": comparisons,
        "method_comparisons": method_comparisons,
        "bootstrap_ci": bootstrap_ci,
        "effect_sizes": effects,
        "method_status": method_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="artifacts/runs/run_registry.csv")
    parser.add_argument("--output", default="artifacts/stats")
    args = parser.parse_args()
    del args.input
    result = analyze_registry(root / args.output)
    print(f"Significance summaries: {len(result['summaries'])}")
    print(f"Paired comparisons: {len(result['comparisons'])}")
    print(f"Method comparisons: {len(result['method_comparisons'])}")
    print(f"Claim safety: {root / args.output / 'claim_safety_report.md'}")


if __name__ == "__main__":
    main()
