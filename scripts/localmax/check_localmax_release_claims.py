from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from localmax_utils import ROOT, protected_hashes_unchanged
from artifacts_v2.canonical_io import write_canonical_json, write_canonical_text


CURRENT_READINESS = "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
RELEASE_ROOT = ROOT / "artifacts" / "localmax_release"
TABLES_DIR = RELEASE_ROOT / "tables"
FIGURES_DIR = RELEASE_ROOT / "figures"
REPORTS_DIR = RELEASE_ROOT / "reports"
CLAIM_MAP_PATH = ROOT / "artifacts" / "claim_map" / "claim_map_localmax.json"


LOCALMAX_DOCS = [
    "docs/LOCALMAX_RELEASE.md",
    "docs/LOCALMAX_RESULTS.md",
    "docs/LOCALMAX_LIMITATIONS.md",
    "docs/LOCALMAX_REPRODUCIBILITY.md",
    "docs/LOCALMAX_CLAIM_BOUNDARY.md",
    "docs/LOCALMAX_MODEL_CARD.md",
    "docs/LOCALMAX_DATA_CARD.md",
    "docs/LOCALMAX_FAILURE_ANALYSIS.md",
    "docs/LOCALMAX_FUTURE_CLOUD_LEVEL3.md",
]
ROOT_DOCS = [
    "PROJECT_SUMMARY.md",
    "PROJECT_ONE_PAGE.md",
    "TECHNICAL_OVERVIEW.md",
    "RESUME_BULLETS.md",
    "DEMO_GUIDE.md",
    "RELEASE_NOTES.md",
    "MANIFEST.md",
    "CHANGELOG.md",
]
RELEASE_TABLES = [
    "localmax_main_results_release.csv",
    "localmax_method_summary_release.csv",
    "localmax_dataset_summary_release.csv",
    "localmax_training_summary_release.csv",
    "localmax_statistical_summary_release.csv",
    "localmax_claim_audit_release.csv",
]
RELEASE_FIGURES = [
    "valid_loss_by_method.png",
    "valid_loss_by_dataset_method.png",
    "urd_vs_raw_valid_loss_difference.png",
    "seed_stability_valid_loss.png",
    "seed_stability_openwebtext_valid_loss.png",
    "seed_stability_c4_valid_loss.png",
    "risk_diversity_cost_tradeoff.png",
    "method_ranking_by_valid_loss.png",
    "method_ranking_openwebtext_valid_loss.png",
    "method_ranking_c4_valid_loss.png",
    "training_strength_summary.png",
    "claim_boundary_summary.png",
]
DISALLOWED_POSITIVE_PATTERNS = [
    r"\bLOCAL_MAX_LEVEL2_5_COMPLETED\b",
    r"\bLEVEL3_COMPLETED_ARTIFACT\b",
    r"\bweak\s+CCF-A\s+achieved\b",
    r"\bCCF-B\s+ready\b",
    r"\bURD(?:-fixed|-Selector)?\s+beats\s+raw\b",
    r"\bSOTA\b",
    r"\bstate[- ]of[- ]the[- ]art\b",
    r"\bofficial\s+downstream\s+completed\b",
    r"\btrue\s+medium\s+completed\b",
    r"\blarge-lite\s+completed\b",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _safe_context(line: str) -> bool:
    text = line.casefold()
    markers = [
        "not ",
        "does not",
        "cannot",
        "disallowed",
        "blocked",
        "claim boundary",
        "false",
        "no ",
        "future",
    ]
    return any(marker in text for marker in markers)


def _scan_claim_text(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in DISALLOWED_POSITIVE_PATTERNS]
    for path in paths:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for lineno, line in enumerate(lines, start=1):
            for pattern, regex in zip(DISALLOWED_POSITIVE_PATTERNS, compiled):
                if regex.search(line) and not _safe_context(line):
                    findings.append(f"{path.relative_to(ROOT).as_posix()}:{lineno}: {pattern}: {line.strip()}")
    return findings


def check_release() -> dict[str, Any]:
    errors: list[str] = []
    for rel in LOCALMAX_DOCS + ROOT_DOCS:
        if not (ROOT / rel).exists():
            errors.append(f"missing document: {rel}")
    for name in RELEASE_TABLES:
        if not (TABLES_DIR / name).exists():
            errors.append(f"missing release table: {name}")
    for name in RELEASE_FIGURES:
        if not (FIGURES_DIR / name).exists():
            errors.append(f"missing release figure: {name}")
    for rel in [
        "artifacts/localmax_release/localmax_release_manifest.json",
        "artifacts/localmax_release/localmax_artifact_registry.jsonl",
        "artifacts/localmax_release/localmax_hashes.json",
        "artifacts/localmax_release/localmax_reproducibility_report.md",
        "artifacts/localmax_release/localmax_limitations_report.md",
        "artifacts/localmax_release/localmax_claim_audit_report.md",
        "artifacts/localmax_release/reports/figure_quality_report.json",
        "artifacts/localmax_release/reports/localmax_claim_audit_report.md",
        "artifacts/reports/step10C_localmax_release_report.json",
        "artifacts/reports/step10C_localmax_release_report.md",
        "artifacts/claim_map/claim_map_localmax.json",
    ]:
        if not (ROOT / rel).exists():
            errors.append(f"missing release artifact: {rel}")

    main_path = TABLES_DIR / "localmax_main_results_release.csv"
    if main_path.exists():
        rows = _read_csv(main_path)
        if len(rows) != 24:
            errors.append(f"release main table must contain 24 rows, found {len(rows)}")
        for index, row in enumerate(rows, start=1):
            if row.get("metric_for_comparison") != "valid_loss":
                errors.append(f"row {index} metric_for_comparison is not valid_loss")
            if row.get("ppl_clipped") not in {"True", "true", "1"}:
                errors.append(f"row {index} does not disclose ppl_clipped=true")
            if row.get("ppl_comparable") not in {"False", "false", "0"}:
                errors.append(f"row {index} does not disclose ppl_comparable=false")
            if not row.get("valid_loss"):
                errors.append(f"row {index} missing valid_loss")
            for field in ["training_manifest", "evaluation_manifest"]:
                value = row.get(field, "")
                if not value or not (ROOT / value).exists():
                    errors.append(f"row {index} missing linked {field}: {value}")

    claim_map = _load_json(CLAIM_MAP_PATH)
    expected_false = [
        "level3_completed_artifact",
        "ccf_b_ready_claimed",
        "weak_ccf_a_claimed",
        "urd_beats_raw_claim_allowed",
        "ppl_improvement_claim_allowed",
        "official_downstream_completed",
        "true_medium_completed",
        "large_lite_completed",
    ]
    if claim_map.get("current_status") != CURRENT_READINESS:
        errors.append("claim map current_status is not the LocalMax release state")
    for key in expected_false:
        if claim_map.get(key) is not False:
            errors.append(f"claim map must keep {key}=false")

    step_report = _load_json(ROOT / "artifacts" / "reports" / "step10C_localmax_release_report.json")
    if step_report.get("current_readiness") != CURRENT_READINESS:
        errors.append("Step 10C report current_readiness mismatch")
    for key in [
        "level3_completed_artifact",
        "ccf_b_ready_claimed",
        "weak_ccf_a_claimed",
        "urd_beats_raw_claimed",
        "ppl_improvement_claimed",
        "official_downstream_completed",
        "true_medium_completed",
        "large_lite_completed",
    ]:
        if step_report.get(key) is not False:
            errors.append(f"Step 10C report must keep {key}=false")

    localmax_release = (
        (ROOT / "docs/LOCALMAX_RELEASE.md").read_text(encoding="utf-8", errors="ignore")
        if (ROOT / "docs/LOCALMAX_RELEASE.md").exists()
        else ""
    )
    if f"Current status: `{CURRENT_READINESS}`" not in localmax_release:
        errors.append("LOCALMAX_RELEASE missing LocalMax current status")
    if "Level 3 status: `not completed`" not in localmax_release:
        errors.append("LOCALMAX_RELEASE missing Level 3 status boundary")

    scanned = [ROOT / rel for rel in LOCALMAX_DOCS + ROOT_DOCS if (ROOT / rel).exists()]
    errors.extend(_scan_claim_text(scanned))
    if not protected_hashes_unchanged():
        errors.append("Protected historical result hashes changed")

    return {
        "status": "passed" if not errors else "failed",
        "localmax_release_claims_passed": not errors,
        "errors": errors,
        "checked_files": [path.relative_to(ROOT).as_posix() for path in scanned],
    }


def main() -> None:
    report = check_release()
    out = REPORTS_DIR / "localmax_release_claim_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json(out, report)
    md = REPORTS_DIR / "localmax_release_claim_check.md"
    lines = [
        "# LocalMax Release Claim Check",
        "",
        f"- Status: `{report['status']}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend([f"- {item}" for item in report["errors"]] or ["- none"])
    write_canonical_text(md, "\n".join(lines))
    if report["status"] != "passed":
        raise SystemExit("LocalMax release claim check failed.\n" + "\n".join(report["errors"]))
    print("LocalMax release claim check: ok")


if __name__ == "__main__":
    main()
