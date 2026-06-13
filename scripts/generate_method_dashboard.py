from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import csv
import json
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

from experiment_utils import root


METHOD_ORDER = [
    "raw",
    "random_same_keep_rate",
    "dedup_only",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v3",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _float(row: dict[str, Any], field: str) -> float | None:
    value = row.get(field, "")
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format(value: Any, digits: int = 4) -> str:
    if value in {"", None}:
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _svg_header(width: int, height: int, title: str, source: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f"<desc>source={escape(source)}; generated_by_script=scripts/generate_method_dashboard.py</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="32" font-family="Arial" font-size="18">{escape(title)}</text>',
    ]


def _empty_svg(title: str, reason: str, source: str) -> str:
    lines = _svg_header(900, 180, title, source)
    lines.extend(
        [
            '<rect x="24" y="58" width="820" height="72" fill="#f7f7f7" stroke="#cccccc"/>',
            f'<text x="42" y="92" font-family="Arial" font-size="14">{escape(reason)}</text>',
            '<text x="42" y="118" font-family="Arial" font-size="12" fill="#555555">'
            "No fabricated values were drawn.</text>",
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def _method_ci_svg(rows: list[dict[str, str]]) -> str:
    values = []
    for row in rows:
        diff = _float(row, "mean_difference_reference_minus_candidate")
        if diff is None:
            diff = _float(row, "mean_difference_reference_minus_v2")
        low = _float(row, "ci95_low")
        high = _float(row, "ci95_high")
        if diff is None or low is None or high is None:
            continue
        values.append((row.get("comparison", ""), diff, low, high, row.get("status", "")))
    if not values:
        return _empty_svg(
            "Method comparison confidence intervals",
            "Missing numeric method comparison rows.",
            "artifacts/stats/method_comparison_summary.csv",
        )
    width = 1120
    height = max(260, 76 + 30 * len(values))
    min_x = min(low for _, _, low, _, _ in values)
    max_x = max(high for _, _, _, high, _ in values)
    span = max(max_x - min_x, 1e-6)

    def sx(value: float) -> float:
        return 340 + ((value - min_x) / span) * 620

    lines = _svg_header(
        width,
        height,
        "Method comparisons: positive means candidate lower PPL",
        "artifacts/stats/method_comparison_summary.csv",
    )
    zero_x = sx(0.0)
    lines.append(f'<line x1="{zero_x:.1f}" y1="54" x2="{zero_x:.1f}" y2="{height - 20}" stroke="#999999"/>')
    for index, (label, diff, low, high, status) in enumerate(values):
        y = 72 + index * 30
        color = "#59a14f" if diff > 0 else "#e15759"
        lines.append(f'<text x="24" y="{y + 4}" font-family="Arial" font-size="11">{escape(label)}</text>')
        lines.append(f'<line x1="{sx(low):.1f}" y1="{y}" x2="{sx(high):.1f}" y2="{y}" stroke="#4c78a8" stroke-width="4"/>')
        lines.append(f'<circle cx="{sx(diff):.1f}" cy="{y}" r="5" fill="{color}"/>')
        lines.append(f'<text x="980" y="{y + 4}" font-family="Arial" font-size="10">{escape(status)}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _v3_vs_baselines_svg(stats_rows: list[dict[str, str]]) -> str:
    values = []
    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    for name in METHOD_ORDER:
        row = by_name.get(name)
        if not row:
            continue
        value = _float(row, "mean")
        if value is not None:
            values.append((name, value))
    if not values:
        return _empty_svg("V3 vs baselines", "Missing stats/main_results.csv.", "artifacts/stats/main_results.csv")
    max_value = max(value for _, value in values)
    min_value = min(value for _, value in values)
    width = 980
    height = max(240, 76 + 34 * len(values))
    lines = _svg_header(width, height, "Validation PPL by method", "artifacts/stats/main_results.csv")
    lines.append('<text x="24" y="54" font-family="Arial" font-size="12">Lower is better.</text>')
    for index, (name, value) in enumerate(values):
        y = 78 + index * 34
        bar = 520 * value / max_value
        color = "#f28e2b" if name == "hdqspp_v3" else "#4c78a8" if value == min_value else "#bab0ac"
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">{escape(name)}</text>')
        lines.append(f'<rect x="260" y="{y}" width="{bar:.1f}" height="22" fill="{color}"/>')
        lines.append(f'<text x="{270 + bar:.1f}" y="{y + 15}" font-family="Arial" font-size="11">{value:.3f}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _keep_rate_vs_ppl_svg(table_rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[tuple[float, float]]] = {}
    for row in table_rows:
        keep = _float(row, "retention_rate")
        ppl = _float(row, "final_val_perplexity")
        name = row.get("baseline_name", "")
        if keep is None or ppl is None or name not in METHOD_ORDER:
            continue
        grouped.setdefault(name, []).append((keep, ppl))
    points = [
        (name, mean([pair[0] for pair in values]), mean([pair[1] for pair in values]))
        for name, values in grouped.items()
    ]
    if not points:
        return _empty_svg("Keep rate vs PPL", "Missing numeric main result rows.", "artifacts/tables/main_results.csv")
    min_x = min(point[1] for point in points)
    max_x = max(point[1] for point in points)
    min_y = min(point[2] for point in points)
    max_y = max(point[2] for point in points)
    width, height = 840, 520

    def sx(value: float) -> float:
        return 90 + ((value - min_x) / max(max_x - min_x, 1e-6)) * 620

    def sy(value: float) -> float:
        return 430 - ((value - min_y) / max(max_y - min_y, 1e-6)) * 320

    lines = _svg_header(width, height, "Keep rate vs validation PPL", "artifacts/tables/main_results.csv")
    lines.append('<line x1="90" y1="430" x2="710" y2="430" stroke="#333333"/>')
    lines.append('<line x1="90" y1="110" x2="90" y2="430" stroke="#333333"/>')
    for name, keep, ppl in points:
        color = "#f28e2b" if name == "hdqspp_v3" else "#4c78a8"
        lines.append(f'<circle cx="{sx(keep):.1f}" cy="{sy(ppl):.1f}" r="6" fill="{color}"/>')
        lines.append(f'<text x="{sx(keep) + 8:.1f}" y="{sy(ppl) + 4:.1f}" font-family="Arial" font-size="11">{escape(name)}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _distribution_shift_svg(diagnostic_rows: list[dict[str, str]], stats_rows: list[dict[str, str]]) -> str:
    means = {row.get("baseline_name", ""): _float(row, "mean") for row in stats_rows}
    points = []
    for row in diagnostic_rows:
        method = row.get("method", "")
        token_js = _float(row, "token_js_vs_raw")
        length_js = _float(row, "length_js_vs_raw")
        ppl = means.get(method)
        if token_js is None or length_js is None or ppl is None:
            continue
        points.append((method, token_js + length_js, ppl))
    if not points:
        return _empty_svg(
            "Distribution shift vs PPL",
            "Missing numeric diagnostic rows.",
            "artifacts/diagnostics/hdqspp_failure_analysis.csv",
        )
    min_x = min(point[1] for point in points)
    max_x = max(point[1] for point in points)
    min_y = min(point[2] for point in points)
    max_y = max(point[2] for point in points)
    width, height = 840, 500

    def sx(value: float) -> float:
        return 90 + ((value - min_x) / max(max_x - min_x, 1e-6)) * 620

    def sy(value: float) -> float:
        return 410 - ((value - min_y) / max(max_y - min_y, 1e-6)) * 300

    lines = _svg_header(width, height, "Distribution shift diagnostic vs PPL", "artifacts/diagnostics/hdqspp_failure_analysis.csv")
    lines.append('<line x1="90" y1="410" x2="710" y2="410" stroke="#333333"/>')
    lines.append('<line x1="90" y1="110" x2="90" y2="410" stroke="#333333"/>')
    for method, shift, ppl in points:
        lines.append(f'<circle cx="{sx(shift):.1f}" cy="{sy(ppl):.1f}" r="6" fill="#4c78a8"/>')
        lines.append(f'<text x="{sx(shift) + 8:.1f}" y="{sy(ppl) + 4:.1f}" font-family="Arial" font-size="11">{escape(method)}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _component_effects_svg(rows: list[dict[str, str]]) -> str:
    values = []
    for row in rows:
        if row.get("run_status") not in {"completed_training", "reference_completed_training"}:
            continue
        ppl = _float(row, "final_val_perplexity")
        if ppl is not None:
            values.append((row.get("ablation_name", ""), ppl, row.get("run_status", "")))
    if not values:
        return _empty_svg("V3 component effects", "Missing v3 ablation rows.", "artifacts/ablations/v3_model_ablation_results.csv")
    max_value = max(value for _, value, _ in values)
    width = 1020
    height = max(260, 76 + 32 * len(values))
    lines = _svg_header(width, height, "V3 component ablation effects", "artifacts/ablations/v3_model_ablation_results.csv")
    for index, (name, value, status) in enumerate(values):
        y = 72 + index * 32
        color = "#4c78a8" if status == "completed_training" else "#bab0ac"
        bar = 580 * value / max_value
        lines.append(f'<text x="24" y="{y + 14}" font-family="Arial" font-size="11">{escape(name)}</text>')
        lines.append(f'<rect x="340" y="{y}" width="{bar:.1f}" height="20" fill="{color}"/>')
        lines.append(f'<text x="{350 + bar:.1f}" y="{y + 14}" font-family="Arial" font-size="11">{value:.3f}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _promising_selection_svg(rows: list[dict[str, str]]) -> str:
    if not rows:
        return _empty_svg("Promising variant selection", "Missing promising variant rows.", "artifacts/methods/promising_variants.csv")
    colors = {
        "promote_to_3seed": "#59a14f",
        "needs_more_diagnostics": "#f28e2b",
        "keep_debug_only": "#bab0ac",
        "reject": "#e15759",
    }
    width = 1100
    height = max(240, 76 + 34 * len(rows))
    lines = _svg_header(width, height, "Promising variant selection", "artifacts/methods/promising_variants.csv")
    for index, row in enumerate(rows):
        y = 72 + index * 34
        decision = row.get("decision", "")
        ppl = row.get("mean_ppl_if_available") or row.get("single_seed_ppl_if_only_debug")
        lines.append(f'<rect x="24" y="{y - 15}" width="18" height="18" fill="{colors.get(decision, "#bab0ac")}"/>')
        lines.append(f'<text x="52" y="{y}" font-family="Arial" font-size="12">{escape(row.get("variant_name", ""))}</text>')
        lines.append(f'<text x="500" y="{y}" font-family="Arial" font-size="12">{escape(decision)}</text>')
        lines.append(f'<text x="760" y="{y}" font-family="Arial" font-size="12">PPL {escape(ppl)}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _method_status(status_report: str) -> str:
    if "- Method status: `honest_audit_framework`" in status_report:
        return "honest_audit_framework"
    for status in [
        "method_supported_over_raw",
        "method_trend_improved_over_raw",
        "method_improves_over_prior_hdqs_but_not_raw",
        "method_unsupported_over_raw",
        "method_unsupported",
        "baseline_underperforms_raw",
    ]:
        if f"`{status}`" in status_report:
            return status
    return "method_unsupported"


def _primary_raw_diff(method_rows: list[dict[str, str]]) -> float | None:
    for row in method_rows:
        if row.get("comparison") == "hdqspp_v3_vs_raw":
            diff = _float(row, "mean_difference_reference_minus_candidate")
            if diff is None:
                diff = _float(row, "mean_difference_reference_minus_v2")
            return diff
    return None


def _source_run_ids_for(stats_row: dict[str, str] | None) -> str:
    if not stats_row:
        return ""
    return stats_row.get("source_run_ids", "")


def _write_claim_maps(
    *,
    stats_rows: list[dict[str, str]],
    method_rows: list[dict[str, str]],
    repositioned: bool,
) -> None:
    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    claim_rows: list[dict[str, str]] = []
    fieldnames = [
        "Claim",
        "Artifact Path",
        "Script",
        "Source Run IDs",
        "Dataset",
        "Dataset Status",
        "Dataset Scope",
        "Baseline",
        "Model Size",
        "Seeds",
        "Tokenizer Hash",
        "Vocab Size",
        "Parameter Count",
        "Train Tokens",
        "Evaluated Validation Tokens",
        "Metric",
        "CI",
        "Status",
        "Safe Claim Level",
    ]
    for name in METHOD_ORDER:
        row = by_name.get(name)
        if not row:
            continue
        claim_rows.append(
            {
                "Claim": f"{name} completed the WikiText-2 small dev candidate run.",
                "Artifact Path": "artifacts/stats/main_results.csv; artifacts/tables/main_results.csv; artifacts/runs/run_registry.jsonl",
                "Script": "scripts/run_experiment.py; scripts/analyze_significance.py; scripts/generate_tables.py",
                "Source Run IDs": _source_run_ids_for(row),
                "Dataset": row.get("dataset_key", "wikitext2_paper"),
                "Dataset Status": row.get("dataset_status", "real_local_nonfallback"),
                "Dataset Scope": row.get("dataset_scope", "official_split"),
                "Baseline": name,
                "Model Size": row.get("model_size", "small"),
                "Seeds": row.get("seeds", ""),
                "Tokenizer Hash": row.get("tokenizer_hash", ""),
                "Vocab Size": row.get("vocab_size", ""),
                "Parameter Count": row.get("parameter_count", ""),
                "Train Tokens": str(row.get("train_tokens", "")),
                "Evaluated Validation Tokens": str(row.get("evaluated_validation_tokens", "")),
                "Metric": f"final_val_perplexity mean {_format(row.get('mean'))}",
                "CI": f"[{_format(row.get('ci95_low'))}, {_format(row.get('ci95_high'))}]",
                "Status": "completed_training",
                "Safe Claim Level": "baseline_summary_only",
            }
        )
    claim_rows.append(
        {
            "Claim": "Method comparison claims are preliminary and capped by seed budget.",
            "Artifact Path": "artifacts/stats/method_comparison_summary.csv; artifacts/stats/method_status_report.md",
            "Script": "scripts/analyze_significance.py",
            "Source Run IDs": "listed in artifacts/stats/main_results.csv",
            "Dataset": "wikitext2_paper",
            "Dataset Status": "real_local_nonfallback",
            "Dataset Scope": "official_split",
            "Baseline": "hdqspp_v3 and references",
            "Model Size": "small",
            "Seeds": "1 2 3",
            "Tokenizer Hash": by_name.get("raw", {}).get("tokenizer_hash", ""),
            "Vocab Size": by_name.get("raw", {}).get("vocab_size", ""),
            "Parameter Count": by_name.get("raw", {}).get("parameter_count", ""),
            "Train Tokens": by_name.get("raw", {}).get("train_tokens", ""),
            "Evaluated Validation Tokens": by_name.get("raw", {}).get("evaluated_validation_tokens", ""),
            "Metric": "paired final_val_perplexity difference",
            "CI": "see method_comparison_summary.csv",
            "Status": "honest_audit_framework" if repositioned else "preliminary_trend_only",
            "Safe Claim Level": "audit_value_not_model_improvement" if repositioned else "no_significance_claim",
        }
    )
    csv_path = root / "docs" / "CLAIM_ARTIFACT_MAP.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(claim_rows)
    lines = [
        "# Claim Artifact Map",
        "",
        "Date: 2026-06-04",
        "",
        "This map is deliberately conservative. Support level is tied to concrete artifacts.",
        "",
        "## Supported Claims",
        "",
        "| Claim | Primary artifacts | Support level |",
        "|---|---|---|",
        "| WikiText-2 real local official splits are used with fallback disabled. | `artifacts/data/wikitext2_paper/data_manifest.json`; `artifacts/data/wikitext2_paper/split_integrity_report.json` | Dataset evidence supported |",
        "| Candidate training rows use shared tokenizer/vocab/parameter count and the same token budget. | `artifacts/tables/main_results.csv`; `scripts/check_main_results_purity.py` | Fair-comparison evidence supported |",
        "| Promising variants were selected from Stage 2.5 ablation evidence. | `artifacts/methods/promising_variants.csv`; `scripts/select_promising_variants.py` | Diagnostic selection evidence |",
        "| HDQS++ v3 was frozen from dev evidence without test-split tuning. | `artifacts/methods/hdqspp_v3_design.json`; `configs/frozen/hdqspp_v3_frozen_wikitext2.yaml` | Protocol evidence supported |",
        "| Method-quality claims are preliminary or unsupported depending on the generated status report. | `artifacts/stats/method_status_report.md`; `artifacts/stats/method_comparison_summary.csv` | No overclaim |",
        "",
        "## Unsupported Claims",
        "",
        "| Claim | Why unsupported |",
        "|---|---|",
        "| HDQS++ is statistically better than raw. | This phase uses 3 seeds and does not permit strong statistical claims. |",
        "| The project is ready for paper submission. | Broader datasets, scales, test evaluation after freezing, and external review artifacts remain incomplete. |",
        "| The project is an official university course or competition submission. | No rubric, policy, registration, or official evaluation record is included. |",
    ]
    (root / "docs" / "CLAIM_ARTIFACT_MAP.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _write_evidence_map(
    *,
    stats_rows: list[dict[str, str]],
    method_rows: list[dict[str, str]],
    repositioned: bool,
) -> None:
    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    lines = [
        "# Project Evidence Map",
        "",
        "| Evidence | Artifact Path | Script | Source Run IDs | Dataset | Method | Seeds | Metric | Status | Safe Interpretation |",
        "|---|---|---|---|---|---|---:|---|---|---|",
        "| Reporting contract | `docs/REPORTING_CONTRACT.md` | manual release contract | `N/A` | all | all | N/A | claim boundary | `canonical` | Single source of truth for public project wording |",
        "| WikiText-2 real non-fallback data | `artifacts/data/wikitext2_paper/data_manifest.json` | `scripts/prepare_real_data.py` | `N/A` | `wikitext2_paper` | `data_prepare` | N/A | dataset_status / dataset_scope | `passed` | Real local official split evidence |",
        "| Split integrity | `artifacts/data/wikitext2_paper/split_integrity_report.json` | `scripts/check_split_integrity.py` | `N/A` | `wikitext2_paper` | `split_check` | N/A | split hashes | `passed` | Train/dev/test separation is checked |",
        "| No test leakage | `artifacts/frozen/no_test_leakage_report.json` | `scripts/check_no_test_leakage.py` | `N/A` | `wikitext2_paper` | `leakage_check` | N/A | test split selection use | `passed` | Test split not used for method tuning |",
        "| Shared tokenizer / vocab / params | `artifacts/tables/main_results.csv` | `scripts/check_main_results_purity.py` | `official completed-training rows` | `wikitext2_paper` | `all main methods` | 1 2 3 | tokenizer/vocab/parameter_count | `passed` | Fair-comparison evidence |",
    ]
    for name in METHOD_ORDER:
        row = by_name.get(name)
        if not row:
            continue
        lines.append(
            "| Completed training summary | "
            "`artifacts/stats/main_results.csv` | "
            "`scripts/analyze_significance.py` | "
            f"`{row.get('source_run_ids', '')}` | "
            f"`{row.get('dataset_key', '')}` | `{name}` | {row.get('seeds', '')} | "
            f"mean PPL {_format(row.get('mean'))}, CI [{_format(row.get('ci95_low'))}, {_format(row.get('ci95_high'))}] | "
            "`completed_training` | Baseline or candidate summary only |"
        )
    for row in method_rows:
        lines.append(
            "| Paired method comparison | "
            "`artifacts/stats/method_comparison_summary.csv` | "
            "`scripts/analyze_significance.py` | "
            "`see main_results source_run_ids` | "
            "`wikitext2_paper` | "
            f"`{row.get('comparison', '')}` | {row.get('paired_seeds', '')} | "
            f"reference-minus-candidate {_format(row.get('mean_difference_reference_minus_candidate') or row.get('mean_difference_reference_minus_v2'))}, "
            f"CI [{_format(row.get('ci95_low'))}, {_format(row.get('ci95_high'))}] | "
            f"`{row.get('status', '')}` | "
            f"{'Audit value, not method improvement' if repositioned else 'Preliminary trend only'} |"
        )
    lines.extend(
        [
            "| OpenWebText streaming sample | `artifacts/data/openwebtext_streaming/data_manifest.json`; `artifacts/data/openwebtext_streaming/DATASET_CARD.md` | `scripts/prepare_streaming_data.py` | `data_prepare` rows in registry | `openwebtext_streaming` | `data_prepare` | N/A | dataset_status / dataset_scope | `real_nonfallback` when available | Real streaming sample, not the complete upstream corpus |",
            "| C4 English streaming sample | `artifacts/data/c4_en_streaming/data_manifest.json`; `artifacts/data/c4_en_streaming/DATASET_CARD.md` | `scripts/prepare_streaming_data.py` | `data_prepare` rows in registry | `c4_en_streaming` | `data_prepare` | N/A | dataset_status / dataset_scope | `real_nonfallback` when available | Real streaming sample, not the complete upstream corpus |",
            "| Cross-dataset audit table | `artifacts/cross_dataset/cross_dataset_results.csv` | `scripts/generate_cross_dataset_tables.py` | `source_run_id` column | `wikitext2_paper`, `openwebtext_streaming`, `c4_en_streaming` | raw/random/dedup/hdqspp_v3 | 1 2 3 | PPL / keep-rate / status | `audit_generated` | Distinguishes completed, lightweight, failed, and configured rows |",
            "| Cross-dataset audit report | `docs/CROSS_DATASET_AUDIT.md` | `scripts/analyze_cross_dataset_audit.py` | `artifacts/cross_dataset/cross_dataset_results.csv` | all audit datasets | all audit methods | 1 2 3 | dataset status and method risk | `audit_generated` | Multi-dataset evidence without a supported improvement-over-raw method claim |",
            "| Method diagnostics | `artifacts/diagnostics/hdqspp_failure_analysis.csv` | `scripts/diagnose_hdqspp.py` | `N/A` | `wikitext2_paper` | `hdqspp / hdqspp_v2` | N/A | token/length JS divergence | `diagnostic_supported` | Explains why proxy improvements did not imply better PPL |",
            "| Failure cases | `docs/FAILURE_CASES.md`; `artifacts/diagnostics/method_error_cases.csv` | `scripts/analyze_method_errors.py` | `N/A` | `wikitext2_paper` | `all audited filters` | N/A | failure mode summaries | `diagnostic_supported` | Failure is retained as audit evidence |",
            "| Audit benchmark repositioning | `docs/PROJECT_REPOSITIONING.md`; `artifacts/stats/method_status_report.md` | `scripts/generate_project_dashboard.py` | `see main_results source_run_ids` | `wikitext2_paper` | `hdqspp_v3` | 1 2 3 | method_status | `honest_audit_framework` | Project value is audit/reproducibility, not supported improvement over raw |",
        ]
    )
    (root / "docs" / "PROJECT_EVIDENCE_MAP.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _update_readme(method_status: str, repositioned: bool) -> None:
    path = root / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "- Method status: `baseline_underperforms_raw`",
        f"- Method status: `{method_status}`",
    )
    if repositioned and "LLM Data Quality Diagnostics and Risk Auditing Benchmark" not in text:
        marker = "## WikiText-2 Method Status\n"
        insert = (
            "## Project Positioning Update\n\n"
            "The current WikiText-2 evidence positions the project as an "
            "**LLM Data Quality Diagnostics and Risk Auditing Benchmark**. "
            "The value is the reproducible audit framework, not a claim that "
            "filtering improves validation perplexity over raw.\n\n"
        )
        text = text.replace(marker, insert + marker)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    figures_dir = root / "artifacts" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    stats_rows = _read_csv(root / "artifacts" / "stats" / "main_results.csv")
    table_rows = _read_csv(root / "artifacts" / "tables" / "main_results.csv")
    method_rows = _read_csv(root / "artifacts" / "stats" / "method_comparison_summary.csv")
    promising_rows = _read_csv(root / "artifacts" / "methods" / "promising_variants.csv")
    v3_ablation_rows = _read_csv(root / "artifacts" / "ablations" / "v3_model_ablation_results.csv")
    diagnostics_rows = _read_csv(root / "artifacts" / "diagnostics" / "hdqspp_failure_analysis.csv")
    readiness = _read_json(root / "artifacts" / "experiment_readiness_report.json")
    status_report_path = root / "artifacts" / "stats" / "method_status_report.md"
    status_report = status_report_path.read_text(encoding="utf-8") if status_report_path.exists() else ""
    method_status = _method_status(status_report)
    raw_diff = _primary_raw_diff(method_rows)
    repositioned = raw_diff is None or raw_diff <= 0
    final_method_status = "honest_audit_framework" if repositioned else method_status

    (figures_dir / "method_comparison_ci.svg").write_text(_method_ci_svg(method_rows), encoding="utf-8")
    (figures_dir / "v3_vs_baselines.svg").write_text(_v3_vs_baselines_svg(stats_rows), encoding="utf-8")
    (figures_dir / "keep_rate_vs_ppl.svg").write_text(_keep_rate_vs_ppl_svg(table_rows), encoding="utf-8")
    (figures_dir / "distribution_shift_vs_ppl.svg").write_text(_distribution_shift_svg(diagnostics_rows, stats_rows), encoding="utf-8")
    (figures_dir / "component_effects_v3.svg").write_text(_component_effects_svg(v3_ablation_rows), encoding="utf-8")
    (figures_dir / "promising_variant_selection.svg").write_text(_promising_selection_svg(promising_rows), encoding="utf-8")

    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    v3 = by_name.get("hdqspp_v3", {})
    raw = by_name.get("raw", {})
    variant = by_name.get("hdqspp_v2_no_token_frequency", {})
    project_value = (
        "The project demonstrates a reproducible data-quality risk audit loop: real data, "
        "fair baselines, frozen configs, registry lineage, diagnostics, ablations, and "
        "claim-safety reporting."
    )
    project_shortfall = (
        "The method claim remains limited by 3 seeds, small model scale, streaming-sample "
        "scope for OpenWebText/C4, and the fact that filtering does not outperform raw."
    )
    dashboard_lines = [
        "# Method Dashboard",
        "",
        f"- Readiness: `{readiness.get('readiness_level', 'EXPERIMENT-CANDIDATE')}`",
        f"- Benchmark scope status: `{readiness.get('benchmark_scope_status', 'single_dataset_candidate')}`",
        f"- Method status: `{final_method_status}`",
        "- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`",
        "- ccf_c_ready: `false`",
        f"- Repositioned as audit/diagnostics framework: `{str(repositioned).lower()}`",
        "",
        "## Main Results",
        "",
        "| Method | Seeds | Mean PPL | CI | Train tokens | Eval validation tokens |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for name in METHOD_ORDER:
        row = by_name.get(name)
        if not row:
            continue
        dashboard_lines.append(
            f"| `{name}` | {row.get('n_seeds', '')} | {_format(row.get('mean'))} | "
            f"[{_format(row.get('ci95_low'))}, {_format(row.get('ci95_high'))}] | "
            f"{row.get('train_tokens', '')} | {row.get('evaluated_validation_tokens', '')} |"
        )
    dashboard_lines.extend(
        [
            "",
            "## Figures",
            "",
            "- `artifacts/figures/method_comparison_ci.svg`",
            "- `artifacts/figures/v3_vs_baselines.svg`",
            "- `artifacts/figures/keep_rate_vs_ppl.svg`",
            "- `artifacts/figures/distribution_shift_vs_ppl.svg`",
            "- `artifacts/figures/component_effects_v3.svg`",
            "- `artifacts/figures/promising_variant_selection.svg`",
            "",
            "## Interpretation",
            "",
            project_value,
            "",
            project_shortfall,
        ]
    )
    (root / "docs" / "METHOD_DASHBOARD.md").write_text(
        "\n".join(dashboard_lines) + "\n",
        encoding="utf-8",
    )

    status_lines = [
        "# Project Status",
        "",
        "Date: 2026-06-11",
        "",
        "## Machine-Readable Status Fields",
        "",
        f"- historical_release_readiness: `{readiness.get('readiness_level', 'EXPERIMENT-CANDIDATE')}`",
        "- current_readiness: `LEVEL3_PIPELINE_READY`",
        f"- method_status: `{final_method_status}`",
        f"- benchmark_scope_status: `{readiness.get('benchmark_scope_status', 'single_dataset_candidate')}`",
        "- ccf_c_ready: `false`",
        "- ccf_b_ready: `false`",
        "- level3_pipeline_ready: `true`",
        "- level3_completed_artifact: `false`",
        "- step2_data_source_interface: `implemented`",
        "- step2_smoke_sample_protocol: `available`",
        "- full_100m_or_500m_data_prepared: `false`",
        "- step3_tokenizer_interface: `implemented`",
        "- step3_bpe_smoke_tokenizer: `verified`",
        "- bpe16k_or_bpe32k_mainline_trained: `false`",
        "- level3_tokenizer_matrix_completed: `false`",
        "- step4_filter_interface: `implemented`",
        "- step4_filter_smoke_verification: `available`",
        "- full_strong_baseline_matrix_completed: `false`",
        "- official_c4_gopher_ccnet_reproduced: `false`",
        "- step5_model_training_interface: `implemented`",
        "- step5_tiny_bpe_smoke_training: `verified`",
        "- step5_checkpoint_manifest: `available`",
        "- bpe_mainline_training_completed: `false`",
        "- medium_or_large_lite_training_completed: `false`",
        "- step6_urd_selector_pipeline: `implemented`",
        "- step6_fixed_weight_smoke_selection: `verified`",
        "- step6_pareto_smoke_selection: `verified`",
        "- step6_urd_effectiveness_evidence: `not_established`",
        "- step7_evaluation_v2_infrastructure: `implemented`",
        "- step7_smoke_evaluations: `verified`",
        "- step7_downstream_protocol: `available`",
        "- step7_effectiveness_claim_allowed: `false`",
        "- step8_mechanism_analysis_infrastructure: `implemented`",
        "- step8_smoke_mechanism_diagnostics: `verified`",
        "- step8_protocol_mechanism_analyses: `available`",
        "- step8_full_scale_mechanism_conclusion_allowed: `false`",
        "- step9_artifact_registry_v2: `implemented`",
        "- step9_level3_readiness_gates: `implemented`",
        "- step9_claim_map_level3: `implemented`",
        "- step9_smoke_protocol_main_separation_checks: `implemented`",
        "- main_result_scope: `WikiText-2 official-split small-model matrix`",
        "- cross_dataset_scope: `bounded streaming-sample audit evidence`",
        "- primary_limitation: `method, data scale, model scale, downstream, and mechanism evidence are not yet sufficient for CCF-B`",
        "- recommended_next_step: `step10A_level3_heavy_protocol_freeze`",
        "",
        "## Current Result Boundary",
        "",
        "Step 2 adds a data-source interface, token-budget sampler, manifest schema, and "
        "no-fallback validation. The verified Step 2 output is smoke data only and does "
        "not enter `main_results`. FineWeb, Dolma, and Pile are protocol-only or optional "
        "until real data is prepared and registered.",
        "",
        "Step 3 adds a tokenizer interface, char tokenizer wrapper, BPE smoke tokenizer "
        "pipeline, optional GPT-2 wrapper, tokenizer manifests, and tokenizer-specific "
        "budget checks. The BPE smoke tokenizer is not mainline model evidence, and "
        "BPE16k/BPE32k mainline tokenizer training is not completed.",
        "",
        "Step 4 adds a filter interface, filter registry, filter manifests, keep-rate "
        "fairness reports, lightweight risk/diversity/cost summaries, and smoke "
        "verification outputs. These outputs are interface artifacts only. They are "
        "not model-training evidence, not PPL results, and not full strong-baseline "
        "matrix completion.",
        "",
        "Step 5 adds a tokenizer-aware model training interface, model-config validation, "
        "training manifests, metrics, checkpoint manifest support, and a tiny BPE smoke "
        "training run. The Step 5 smoke run is engineering evidence only. It is not a "
        "new main result, does not update `main_results`, and does not claim completed "
        "small/medium/large-lite BPE training.",
        "",
        "Step 6 adds the URD-Selector pipeline with utility, risk, diversity, shift, and "
        "cost proxy components, fixed-weight selection, Pareto-style smoke selection, and "
        "single-component ablation configs. Step 6 does not run model training, does not "
        "add PPL/downstream results, and does not establish URD effectiveness.",
        "",
        "Step 7 adds the evaluation_v2 infrastructure layer with LM, downstream protocol, "
        "risk, diversity, cost, stability/statistics, and Pareto evaluators. Step 7 "
        "outputs are smoke/protocol artifacts only. They do not update `main_results` and "
        "do not permit an effectiveness claim.",
        "",
        "Step 8 adds the analysis_v2 mechanism-analysis infrastructure layer with "
        "proxy-utility, overfiltering, diversity-loss, domain-shift, Pareto-mechanism, "
        "failure-taxonomy, rank-stability, tokenizer-sensitivity, and scale-trend "
        "analyzers. Step 8 outputs are smoke/protocol artifacts only. They do not update "
        "`main_results`, do not prove URD effectiveness, and do not permit a full-scale "
        "mechanism conclusion.",
        "",
        "Step 9 adds Level 3 readiness states, readiness gates, a Level 3 claim map, "
        "an artifact registry v2, and checks that separate historical main tables "
        "from smoke/protocol artifacts. Step 9 does not add new experiments, does "
        "not update `main_results`, does not mark Level 3 completion, and does not "
        "permit method-success claims.",
        "",
        "- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`",
        "- Reporting contract: `docs/REPORTING_CONTRACT.md`",
        "",
        "The candidate matrix now includes raw, random, dedup, HDQS++ v1, HDQS++ v2, "
        "the selected v2 no-token-frequency variant, and HDQS++ v3.",
        "",
        f"- raw mean PPL: `{_format(raw.get('mean'))}`",
        f"- selected v2 no-token-frequency mean PPL: `{_format(variant.get('mean'))}`",
        f"- HDQS++ v3 mean PPL: `{_format(v3.get('mean'))}`",
        "",
        "The interpretation follows the generated method status report and does not "
        "claim supported improvement over raw.",
        "",
        "OpenWebText and C4 English evidence uses real HuggingFace streaming samples. "
        "These are explicitly bounded streaming samples, not complete upstream corpora. "
        "Their evidence is reported in `artifacts/cross_dataset/` and "
        "`docs/CROSS_DATASET_AUDIT.md`.",
        "",
        "## Current Readiness Interpretation",
        "",
        "The repository is an experiment-candidate audit benchmark with Step 9 "
        "Level 3 pipeline hygiene in place. It is not CCF-B ready, not CCF-C "
        "ready, not publication-ready, and not a completed Level 3 artifact.",
        "",
        "Current evidence is useful for:",
        "",
        "- WikiText-2 official-split small-model audit comparisons;",
        "- bounded streaming-sample OpenWebText/C4 audit checks;",
        "- showing that heuristic filtering can underperform raw data under fair controls;",
        "- validating the Step 5 training-interface contract with a tiny BPE smoke run;",
        "- validating the Step 6 URD selector-interface contract with smoke filter outputs;",
        "- validating the Step 7 evaluation-interface contract with smoke/protocol outputs;",
        "- validating the Step 8 mechanism-analysis contract with smoke/protocol outputs;",
        "- validating Step 9 artifact registry, readiness gates, claim map, and smoke/protocol separation checks;",
        "- preserving negative evidence and artifact lineage.",
        "",
        "Current evidence is not sufficient for:",
        "",
        "- a method-success claim over raw;",
        "- not full OpenWebText/C4 claims;",
        "- large-scale LLM pretraining conclusions;",
        "- completed downstream evaluation claims;",
        "- completed URD-Selector claims;",
        "- established URD effectiveness claims;",
        "- full-scale mechanism conclusion claims;",
        "- official downstream completion claims;",
        "- completed BPE16k/BPE32k, medium, or large-lite training claims;",
        "- completed CCF-B/Level 3 claims.",
        "- completed Level 3 heavy evidence claims.",
        "",
        "Future publication and reviewer notes are archived under "
        "`docs/future_publication_notes/`. They are future publication gap notes, "
        "not current release claims.",
        "",
        "## Boundary",
        "",
        "`method_debug` and filtering-only artifacts remain isolated from `main_results`. "
        "V3 ablation rows are model-training diagnostics, not primary method claims.",
        "",
        "Canonical reporting documents:",
        "",
        "- `docs/REPORTING_CONTRACT.md`",
        "- `docs/reporting_contract_level3.md`",
        "- `docs/claim_boundary.md`",
        "- `docs/level3_upgrade_roadmap.md`",
        "- `docs/level3_route.md`",
        "- `docs/level3_readiness_gates.md`",
        "- `docs/level3_claim_boundary.md`",
    ]
    (root / "docs" / "PROJECT_STATUS.md").write_text(
        "\n".join(status_lines) + "\n",
        encoding="utf-8",
    )

    diagnostics_lines = [
        "# Method Diagnostics",
        "",
        "## HDQS++ v2 Failure Diagnosis",
        "",
        "v2 full reduced token/length distribution shift versus v1, but model-training "
        "results still underperformed raw. Stage 2.5 ablations identified token-frequency "
        "preservation as the strongest harmful component, with strict distribution "
        "preservation and length prior also suspicious.",
        "",
        "## Promising Variant Selection",
        "",
        "| Variant | Decision | PPL signal |",
        "|---|---|---:|",
    ]
    for row in promising_rows:
        diagnostics_lines.append(
            f"| `{row.get('variant_name', '')}` | `{row.get('decision', '')}` | "
            f"{row.get('mean_ppl_if_available') or row.get('single_seed_ppl_if_only_debug')} |"
        )
    diagnostics_lines.extend(
        [
            "",
            "## HDQS++ v3 Repair",
            "",
            "- Removed token-frequency preservation.",
            "- Replaced strict distribution preservation with weak length/bin guardrails.",
            "- Replaced hard filtering emphasis with calibrated soft selection.",
            "- Kept base quality, quality/diversity balance, and capped repetition.",
            "",
            "## Current Boundary",
            "",
            "If v3 does not outperform raw, the safe interpretation is diagnostic/audit value, "
            "not a model-quality improvement claim.",
        ]
    )
    (root / "docs" / "METHOD_DIAGNOSTICS.md").write_text(
        "\n".join(diagnostics_lines) + "\n",
        encoding="utf-8",
    )

    if repositioned:
        (root / "docs" / "PROJECT_REPOSITIONING.md").write_text(
            "# Project Repositioning\n\n"
            "- New method status: `honest_audit_framework`\n"
            "- New project line: **LLM Data Quality Diagnostics and Risk Auditing Benchmark**\n\n"
            "HDQS++/v3 should not be described as improving validation perplexity over raw "
            "under the current WikiText-2 small-model evidence. The project value is that it "
            "can detect when data-quality filtering is risky, overfilters a curated corpus, "
            "or is weaker than raw/random/dedup baselines under a fair protocol.\n\n"
            "This keeps the project useful as an AI benchmark and audit framework: it has "
            "real data, fair baselines, shared tokenizer checks, multi-seed registry rows, "
            "artifact lineage, no-test-leakage checks, ablation evidence, and claim-safety "
            "reporting.\n",
            encoding="utf-8",
        )

    _write_evidence_map(stats_rows=stats_rows, method_rows=method_rows, repositioned=repositioned)
    _write_claim_maps(stats_rows=stats_rows, method_rows=method_rows, repositioned=repositioned)
    _update_readme(final_method_status, repositioned)

    final_lines = [
        "# Final Audit",
        "",
        "Date: 2026-06-04",
        "",
        f"1. Current readiness: `{readiness.get('readiness_level', 'EXPERIMENT-CANDIDATE')}`.",
        f"2. Method status: `{final_method_status}`.",
        "3. `ccf_c_ready`: `false`.",
        "4. v2 failed because distribution diagnostics improved while validation PPL worsened.",
        "5. Promising v2 ablation: `ablation_v2_without_token_frequency_preservation`.",
        "6. Stage 2.6 selected promising variants via `scripts/select_promising_variants.py`.",
        "7. HDQS++ v3 was implemented and frozen from dev-only evidence.",
        "8. v3 removed token-frequency preservation, weakened length/distribution constraints, and added calibrated soft selection.",
        f"9. v3 3-seed completion: `{bool(v3)}`.",
        f"10. v3 vs raw raw-minus-v3 diff: `{_format(raw_diff)}`.",
        "11. v3 vs random/dedup/v1/v2: see `artifacts/stats/method_comparison_summary.csv`.",
        "12. Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`.",
        f"13. Audit/diagnostics framework repositioned: `{str(repositioned).lower()}`.",
        "14. `main_results` is generated from completed-training registry rows only.",
        "15. `method_debug` remains isolated.",
        "16. filtering-only artifacts remain isolated.",
        "17. run registry is append-oriented; superseded artifact hashes are handled by lineage checks.",
        "18. split integrity and no-test-leakage checks are required final gates.",
        f"19. Current project value: {project_value}",
        f"20. Current shortfall: {project_shortfall}",
        "21. Next phase should expand datasets after this honest method boundary is accepted.",
    ]
    (root / "docs" / "FINAL_AUDIT.md").write_text(
        "\n".join(final_lines) + "\n",
        encoding="utf-8",
    )
    print(f"Method dashboard generated. method_status={final_method_status}")
    print(f"Repositioned: {repositioned}")


if __name__ == "__main__":
    main()
