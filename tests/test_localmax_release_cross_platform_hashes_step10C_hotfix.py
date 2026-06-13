from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_cross_platform_hash_report_declares_canonical_policy() -> None:
    report = json.loads((ROOT / "artifacts/localmax_release/reports/cross_platform_hash_report.json").read_text(encoding="utf-8"))

    assert report["canonical_newline"] == "LF"
    assert report["encoding"] == "UTF-8"
    assert report["claim_checker_idempotent"] is True
    assert report["release_finalizer_idempotent"] is True
    assert report["localmax_registry_hash_check_passed"] is True
    assert report["cross_platform_rewrite_detected"] is False
    assert report["timestamp_causes_frozen_hash_drift"] is False


def test_generated_text_artifacts_use_lf_newlines() -> None:
    targets = [
        ROOT / "artifacts/localmax_release/reports/localmax_release_claim_check.json",
        ROOT / "artifacts/localmax_release/reports/localmax_release_claim_check.md",
        ROOT / "artifacts/localmax_release/reports/figure_quality_report.json",
        ROOT / "artifacts/localmax_release/reports/release_bundle_integrity_report.md",
        ROOT / "artifacts/reports/step10C_localmax_release_report.json",
        ROOT / "docs/LOCALMAX_RELEASE.md",
    ]
    for path in targets:
        data = path.read_bytes()
        assert b"\r\n" not in data, path
        assert data.endswith(b"\n"), path

