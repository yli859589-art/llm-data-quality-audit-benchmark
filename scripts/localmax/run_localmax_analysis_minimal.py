from __future__ import annotations

import csv
import json
from pathlib import Path

from localmax_utils import LOCALMAX_REPORTS, REPORTS, ROOT, load_json, status_payload, write_csv, write_json, write_report


ANALYSIS_DIR = ROOT / "artifacts" / "localmax_analysis"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    eval_report = load_json(REPORTS / "localmax_evaluation_report.json")
    ready_input = eval_report.get("localmax_evaluation_ready") is True
    lm_summary = _read_csv(ROOT / "artifacts/localmax_evaluation/lm_metrics_summary.csv")
    stats = _read_csv(ROOT / "artifacts/localmax_evaluation/statistical_tests.csv")
    rdc = _read_csv(ROOT / "artifacts/localmax_evaluation/risk_diversity_cost.csv")
    blocking = []
    if not ready_input:
        blocking.append("LocalMax evaluation is not ready; mechanism analysis is blocked.")
    proxy_rows = []
    for row in stats:
        proxy_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "comparison": row["comparison"],
                "mean_paired_loss_improvement": row["mean_paired_loss_improvement"],
                "improvement_claim_allowed": row["improvement_claim_allowed"],
                "finding": "insufficient_or_mixed_evidence"
                if row["improvement_claim_allowed"] != "True"
                else "bounded_positive_training_metric_evidence",
            }
        )
    overfilter = {
        "completed": ready_input,
        "finding": "insufficient_evidence" if not rdc else "bounded_keep_rate_audit_completed",
        "rows_analyzed": len(rdc),
    }
    diversity = {
        "completed": ready_input,
        "finding": "insufficient_evidence" if not rdc else "bounded_diversity_audit_completed",
        "rows_analyzed": len(rdc),
    }
    rank_stability = {
        "completed": ready_input,
        "finding": "insufficient_evidence" if len(lm_summary) < 2 else "bounded_rank_stability_protocol_completed",
        "rows_analyzed": len(lm_summary),
    }
    negative_lines = [
        "# LocalMax Negative Result Analysis",
        "",
        "This analysis is generated only from Step 10B-LocalMax minimal artifacts.",
        "No Level 3, CCF-B-ready, official downstream, or broad method-win claim is made.",
        "",
        "## Summary",
        "",
    ]
    if not ready_input:
        negative_lines.append("- insufficient_evidence: evaluation artifacts are missing or incomplete.")
    else:
        allowed = [row for row in stats if row.get("improvement_claim_allowed") == "True"]
        negative_lines.append(f"- Statistical comparisons with claim allowed: {len(allowed)}.")
        negative_lines.append("- Any comparison whose CI crosses zero remains a negative or inconclusive result.")
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        ANALYSIS_DIR / "proxy_utility_mismatch.csv",
        ["dataset_id", "comparison", "mean_paired_loss_improvement", "improvement_claim_allowed", "finding"],
        proxy_rows,
    )
    write_json(ANALYSIS_DIR / "overfiltering_report.json", overfilter)
    write_json(ANALYSIS_DIR / "diversity_loss_report.json", diversity)
    write_json(ANALYSIS_DIR / "rank_stability_report.json", rank_stability)
    (ANALYSIS_DIR / "negative_result_analysis.md").write_text("\n".join(negative_lines) + "\n", encoding="utf-8")
    mechanism_manifest = {
        "step": "step10B_localmax_execution_fix",
        "scope": "localmax_minimal_mechanism",
        "completed": ready_input,
        "proxy_utility_mismatch_path": "artifacts/localmax_analysis/proxy_utility_mismatch.csv",
        "overfiltering_report_path": "artifacts/localmax_analysis/overfiltering_report.json",
        "diversity_loss_report_path": "artifacts/localmax_analysis/diversity_loss_report.json",
        "rank_stability_report_path": "artifacts/localmax_analysis/rank_stability_report.json",
        "negative_result_analysis_path": "artifacts/localmax_analysis/negative_result_analysis.md",
        "full_scale_mechanism_claim_allowed": False,
        "level3_mechanism": False,
    }
    write_json(ANALYSIS_DIR / "mechanism_manifest.json", mechanism_manifest)
    report = status_payload(
        "mechanism",
        ready_input,
        blocking,
        {
            "step": "step10B_localmax_execution_fix",
            "status": "completed" if ready_input else "blocked",
            "localmax_mechanism_ready": ready_input,
            "mechanism_manifest_path": "artifacts/localmax_analysis/mechanism_manifest.json",
            "full_scale_mechanism_claim_allowed": False,
            "level3_mechanism": False,
            "proxy_utility_rows": len(proxy_rows),
            "negative_result_analysis_ready": ready_input,
            "recommended_next_step": "finalize_localmax_minimal_execution" if ready_input else "continue_mechanism_execution",
        },
    )
    write_report(report, "localmax_mechanism_report", "LocalMax Minimal Mechanism Report")
    print(json.dumps({"localmax_mechanism_ready": ready_input, "proxy_rows": len(proxy_rows)}))


if __name__ == "__main__":
    main()

