from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccfc_utils import CCFC_TABLES, ROOT, load_json, protected_hashes, protected_hashes_unchanged, status_payload, write_json, write_report, write_text


def _gate(name: str, report_name: str, key: str) -> dict[str, Any]:
    report = load_json(ROOT / "artifacts" / "reports" / report_name)
    return {
        "gate": name,
        "report": f"artifacts/reports/{report_name}",
        "passed": bool(report.get(key)),
        "status": report.get("status", "missing"),
        "current_readiness": report.get("current_readiness", ""),
        "blocking_failures": report.get("blocking_failures", []),
    }


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> None:
    filter_report = load_json(ROOT / "artifacts" / "reports" / "localmax_ccfc_filter_report.json")
    training_report = load_json(ROOT / "artifacts" / "reports" / "localmax_ccfc_training_report.json")
    eval_report = load_json(ROOT / "artifacts" / "reports" / "localmax_ccfc_evaluation_report.json")
    downstream_report = load_json(ROOT / "artifacts" / "reports" / "localmax_ccfc_downstream_report.json")
    gates = [
        _gate("filter_matrix", "localmax_ccfc_filter_report.json", "ccfc_filters_ready"),
        _gate("five_m_training_matrix", "localmax_ccfc_training_report.json", "ccfc_training_ready"),
        _gate("evaluation_matrix", "localmax_ccfc_evaluation_report.json", "ccfc_evaluation_ready"),
        _gate("local_downstream_probe", "localmax_ccfc_downstream_report.json", "downstream_completed"),
    ]
    passed = {gate["gate"]: gate["passed"] for gate in gates}
    ccf_c_candidate_ready = all(passed.values())
    blocking = []
    for gate in gates:
        if not gate["passed"]:
            blocking.append(f"{gate['gate']} not complete: {gate['status']}")
            blocking.extend(str(item) for item in gate.get("blocking_failures", []))
    readiness = status_payload(
        "ccfc_readiness",
        ccf_c_candidate_ready,
        blocking,
        {
            "status": "completed" if ccf_c_candidate_ready else "completed_with_gaps",
            "current_readiness": "TOP_TIER_CCFC_PROJECT_CANDIDATE" if ccf_c_candidate_ready else "CCFC_STRENGTHENING_IN_PROGRESS",
            "ccfc_candidate_ready": ccf_c_candidate_ready,
            "ccf_c_paper_claimed": False,
            "ccf_b_ready_claimed": False,
            "gates": gates,
            "filter_methods": filter_report.get("methods_completed", []),
            "completed_training_runs": training_report.get("completed_core_runs", 0),
            "expected_training_runs": training_report.get("expected_core_runs", 42),
            "target_tokens_seen_per_run": training_report.get("target_tokens_seen_per_run", 5000000),
            "best_method_by_valid_nll": eval_report.get("best_method_by_valid_nll", {}),
            "local_cloze_probe_rows": downstream_report.get("completed_rows", 0),
            "historical_results_modified": not protected_hashes_unchanged(),
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "finish_ccfc_training_matrix" if not ccf_c_candidate_ready else "write_submission_style_paper",
        },
    )
    write_report(readiness, "localmax_ccfc_readiness_report", "LocalMax CCF-C Candidate Readiness Report")
    write_json(ROOT / "artifacts" / "reports" / "localmax_ccfc_readiness_report.json", readiness)
    claim_doc = """# LocalMax CCF-C Candidate Claim Boundary

Allowed current claims:

- The repository contains a CCF-C-oriented strengthening line built on LocalMax V2.
- The strengthening line adds stronger data-filter baselines: random same-keep-rate, C4-style quality filtering, and perplexity-proxy filtering.
- The project may report completed gates only when their machine-readable readiness reports pass.

Forbidden current claims:

- Do not claim CCF-C acceptance.
- Do not claim CCF-B readiness.
- Do not claim Level 3 completion.
- Do not claim URD beats raw, length filtering, or stronger baselines unless the CCF-C statistical table allows it.
- Do not claim official downstream benchmark completion from local cloze probes.
"""
    write_text(ROOT / "docs" / "LOCALMAX_CCFC_CLAIM_BOUNDARY.md", claim_doc)
    report = f"""# LocalMax CCF-C Candidate Project Report

## Executive Summary

This project is being strengthened from a LocalMax V2 research artifact into a CCF-C-oriented AI research prototype. The target claim is not a paper acceptance claim; it is a project-level claim that the repository contains a reproducible, multi-dataset, multi-baseline audit benchmark for language-model pretraining data filtering under local compute constraints.

Current readiness: `{readiness['current_readiness']}`

## Research Question

Do language-model pretraining data filters actually improve language-model utility under controlled token budgets, and when do simple baselines such as length filtering outperform more complex quality selectors?

## Added CCF-C Strengthening Evidence

- Stronger baseline matrix: `raw`, `exact_dedup`, `length_filter`, `random_same_keep_rate`, `c4_quality_filter`, `perplexity_proxy_filter`, `urd_fixed`.
- Target training depth: 5M tokens_seen per run.
- Target matrix: 2 datasets x 7 methods x 3 seeds = 42 runs.
- Metric: per-token validation NLL/log-PPL/PPL with no PPL clipping.
- Downstream: local LAMBADA-style cloze probe only; no official downstream claim.

## Gate Status

| Gate | Passed | Report |
| --- | --- | --- |
"""
    for gate in gates:
        report += f"| {gate['gate']} | {gate['passed']} | `{gate['report']}` |\n"
    report += f"""
## Current Quantitative Status

- Filter methods completed: `{filter_report.get('methods_completed', [])}`
- Completed training runs: `{training_report.get('completed_core_runs', 0)}` / `{training_report.get('expected_core_runs', 42)}`
- Best method by valid NLL: `{eval_report.get('best_method_by_valid_nll', {})}`
- Local cloze probe rows: `{downstream_report.get('completed_rows', 0)}`

## What Would Make This Top-Tier CCF-C Complete

1. Finish all 42 strengthened training runs at >=5M tokens_seen/run.
2. Generate evaluation/statistical tables from the full matrix.
3. Complete local cloze probes for representative methods.
4. Write the final submission-style paper around the honest audit/negative-result finding.

## Claim Hygiene

This report does not claim CCF-C acceptance, CCF-B readiness, Level 3 completion, SOTA, or unsupported URD superiority.
"""
    write_text(ROOT / "docs" / "LOCALMAX_CCFC_PROJECT_REPORT.md", report)
    print(json.dumps({"ccfc_candidate_ready": ccf_c_candidate_ready, "current_readiness": readiness["current_readiness"]}))
    if not ccf_c_candidate_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
