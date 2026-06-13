from __future__ import annotations

import json
import sys
from pathlib import Path

from artifacts_v2.registry import read_registry, write_registry
from artifacts_v2.validation import validate_registry_file


ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
import run_all_checks as rac  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_report_rewrite_after_registry_generation_causes_hash_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    report = root / "artifacts/reports/step10A_readiness_report.json"
    _write_json(report, {"step": "step10A_level3_heavy_protocol_freeze", "protocol_only": True, "completed": False})
    registry_path, _summary_path, _records = write_registry(root)

    _write_json(
        report,
        {
            "step": "step10A_level3_heavy_protocol_freeze",
            "protocol_only": True,
            "completed": False,
            "rewritten": True,
        },
    )

    errors = validate_registry_file(registry_path, root)
    assert any("hash mismatch: artifacts/reports/step10A_readiness_report.json" in error for error in errors)


def test_registry_regeneration_fixes_report_hash_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    report = root / "artifacts/reports/step10A_readiness_report.json"
    _write_json(report, {"step": "step10A_level3_heavy_protocol_freeze", "protocol_only": True, "completed": False})
    registry_path, _summary_path, _records = write_registry(root)
    _write_json(report, {"step": "step10A_level3_heavy_protocol_freeze", "protocol_only": True, "completed": False, "rewritten": True})

    assert validate_registry_file(registry_path, root)

    registry_path, _summary_path, _records = write_registry(root)
    assert validate_registry_file(registry_path, root) == []
    rows = read_registry(registry_path)
    assert any(row["path"] == "artifacts/reports/step10A_readiness_report.json" and row["step"] == "step10A" for row in rows)


def test_run_all_checks_finalizes_registry_after_report_generating_checks() -> None:
    groups = list(rac._check_groups(skip_tests=True))

    assert groups.index("level3_gate_checks") < groups.index("registry_finalization_checks")
    assert groups.index("claim_checks") < groups.index("registry_finalization_checks")
    assert groups.index("artifact_checks") < groups.index("registry_finalization_checks")

    final_commands = [
        command.command
        for command in rac._check_groups(skip_tests=True)["registry_finalization_checks"].commands
    ]
    assert [sys.executable, "scripts/finalize_artifact_registry_v2.py"] in final_commands
    assert [sys.executable, "scripts/check_registry_to_tables.py"] in final_commands
    assert [sys.executable, "scripts/check_main_results_from_registry.py"] in final_commands

