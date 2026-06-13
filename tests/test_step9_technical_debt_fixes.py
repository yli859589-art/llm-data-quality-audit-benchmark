from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_step5_debt_is_recorded_without_promoting_smoke_training() -> None:
    report = _load_json("artifacts/reports/step5_readiness_report.json")
    assert report.get("resume_supported") is False
    assert report.get("independent_eval_split_supported") is False or report.get("eval_split_supported") is False

    registry_rows = [
        json.loads(line)
        for line in (ROOT / "artifacts/training_step5/training_registry.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert registry_rows
    assert all(row.get("run_id") for row in registry_rows)
    assert all(row.get("created_at") for row in registry_rows)
    assert all(row.get("manifest_path") for row in registry_rows)
    assert all(row.get("manifest_hash") for row in registry_rows)


def test_step6_urd_debt_fields_are_present() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "URD-Selector is implemented as a smoke-verified selector pipeline" in readme
    assert "not yet effectiveness-verified or current main evidence" in readme

    manifests = sorted((ROOT / "artifacts/filter_outputs_step6").glob("**/filter_manifest.json"))
    assert manifests
    for manifest in manifests:
        payload = _load_json(manifest.relative_to(ROOT).as_posix())
        if payload.get("method_family") == "URD-Selector":
            assert payload.get("urd_extension_version") == "step6.urd_manifest.v1"
            assert payload.get("ablation_evaluation_scope") in {
                "not_full_ablation_evaluation",
                "single_component_ablation_smoke_only",
            }


def test_step7_and_step8_debt_boundaries_are_recorded() -> None:
    combined = (ROOT / "configs/evaluation/combined_smoke.yaml").read_text(encoding="utf-8")
    assert "runner_status" in combined
    assert "config_only" in combined

    stability = _load_json("artifacts/evaluation_step7/stability_protocol/evaluation_manifest.json")
    assert stability.get("protocol_only") is True
    assert stability.get("evidence_status") == "insufficient_evidence"

    step8 = _load_json("artifacts/reports/step8_readiness_report.json")
    assert step8.get("run_all_checks_passed") is True

    manifest = ROOT / "artifacts/analysis_step8/wikitext2_smoke/proxy_utility_urd_fixed/mechanism_manifest.json"
    result = subprocess.run(
        [sys.executable, "scripts/check_mechanism_manifests.py", "--path", str(manifest)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    assert "Mechanism manifest check: ok" in result.stdout
