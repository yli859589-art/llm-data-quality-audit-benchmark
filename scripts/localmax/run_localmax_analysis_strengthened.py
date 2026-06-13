from __future__ import annotations

import csv
import json
from pathlib import Path

from localmax_utils import ROOT, load_json, status_payload, write_csv, write_json, write_report


OUTPUT_DIR = ROOT / "artifacts" / "localmax_analysis_strengthened"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    eval_report = load_json(ROOT / "artifacts" / "reports" / "localmax_evaluation_strengthened_report.json")
    stats = _read_csv(ROOT / "artifacts" / "localmax_evaluation_strengthened" / "statistical_tests.csv")
    ranking = _read_csv(ROOT / "artifacts" / "localmax_evaluation_strengthened" / "method_ranking.csv")
    rdc = _read_csv(ROOT / "artifacts" / "localmax_evaluation_strengthened" / "risk_diversity_cost.csv")
    ready = eval_report.get("localmax_evaluation_strengthened_ready") is True
    blocking = [] if ready else ["Strengthened evaluation is not ready."]
    proxy_rows = [
        {
            "dataset_id": row["dataset_id"],
            "comparison": row["comparison"],
            "mean_paired_loss_improvement": row["mean_paired_loss_improvement"],
            "improvement_claim_allowed": row["improvement_claim_allowed"],
            "finding": "claim_allowed" if row["improvement_claim_allowed"] == "True" else "insufficient_or_negative_evidence",
        }
        for row in stats
    ]
    urd_rows = [row for row in stats if row["comparison"] == "urd_fixed_vs_raw"]
    urd = {
        "full_mechanism_claim_allowed": False,
        "insufficient_evidence": True,
        "datasets": {
            row["dataset_id"]: {
                "mean_paired_loss_improvement": row["mean_paired_loss_improvement"],
                "ci_low": row["ci_low"],
                "ci_high": row["ci_high"],
                "improvement_claim_allowed": row["improvement_claim_allowed"] == "True",
            }
            for row in urd_rows
        },
    }
    overfilter = {
        "completed": ready,
        "rows_analyzed": len(rdc),
        "full_mechanism_claim_allowed": False,
        "insufficient_evidence": True,
        "finding": "minimal strengthened local mechanism diagnostics only",
    }
    diversity = {
        "completed": ready,
        "rows_analyzed": len(rdc),
        "full_mechanism_claim_allowed": False,
        "insufficient_evidence": True,
        "finding": "minimal strengthened diversity diagnostics only",
    }
    rank = {
        "completed": ready,
        "rows_analyzed": len(ranking),
        "full_mechanism_claim_allowed": False,
        "insufficient_evidence": True,
        "finding": "rank stability is local and bounded to strengthened minimal runs",
    }
    negative_lines = [
        "# LocalMax Strengthened Negative Result Analysis",
        "",
        "This report is based on strengthened LocalMax artifacts only.",
        "It does not make a full-scale mechanism conclusion, Level 3 claim, CCF-B-ready claim, or broad URD-win claim.",
        "",
        "## Statistical Guardrails",
        "",
        "- Comparisons use `valid_loss`; clipped PPL is reference-only.",
        "- Improvement is disallowed when the confidence interval crosses zero.",
        "- If URD fixed does not beat raw under the guarded comparison, that negative result is retained.",
    ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUTPUT_DIR / "proxy_utility_mismatch.csv",
        ["dataset_id", "comparison", "mean_paired_loss_improvement", "improvement_claim_allowed", "finding"],
        proxy_rows,
    )
    write_json(OUTPUT_DIR / "overfiltering_report.json", overfilter)
    write_json(OUTPUT_DIR / "diversity_loss_report.json", diversity)
    write_json(OUTPUT_DIR / "rank_stability_report.json", rank)
    write_json(OUTPUT_DIR / "urd_vs_raw_analysis.json", urd)
    (OUTPUT_DIR / "negative_result_analysis.md").write_text("\n".join(negative_lines) + "\n", encoding="utf-8")
    manifest = {
        "step": "step10B_localmax_training_strengthen",
        "scope": "localmax_mechanism_strengthened",
        "completed": ready,
        "proxy_utility_mismatch_path": "artifacts/localmax_analysis_strengthened/proxy_utility_mismatch.csv",
        "overfiltering_report_path": "artifacts/localmax_analysis_strengthened/overfiltering_report.json",
        "diversity_loss_report_path": "artifacts/localmax_analysis_strengthened/diversity_loss_report.json",
        "rank_stability_report_path": "artifacts/localmax_analysis_strengthened/rank_stability_report.json",
        "urd_vs_raw_analysis_path": "artifacts/localmax_analysis_strengthened/urd_vs_raw_analysis.json",
        "negative_result_analysis_path": "artifacts/localmax_analysis_strengthened/negative_result_analysis.md",
        "full_mechanism_claim_allowed": False,
        "insufficient_evidence": True,
        "level3_mechanism": False,
    }
    write_json(OUTPUT_DIR / "mechanism_manifest.json", manifest)
    report = status_payload(
        "mechanism_strengthened",
        ready,
        blocking,
        {
            "step": "step10B_localmax_training_strengthen",
            "status": "completed" if ready else "blocked",
            "localmax_mechanism_strengthened_ready": ready,
            "mechanism_manifest_path": "artifacts/localmax_analysis_strengthened/mechanism_manifest.json",
            "full_mechanism_claim_allowed": False,
            "insufficient_evidence": True,
            "proxy_utility_rows": len(proxy_rows),
            "urd_vs_raw_analysis_path": "artifacts/localmax_analysis_strengthened/urd_vs_raw_analysis.json",
            "level3_mechanism": False,
        },
    )
    write_report(report, "localmax_mechanism_strengthened_report", "LocalMax Mechanism Strengthened Report")
    print(json.dumps({"localmax_mechanism_strengthened_ready": ready, "proxy_rows": len(proxy_rows)}))


if __name__ == "__main__":
    main()

