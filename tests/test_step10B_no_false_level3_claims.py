from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path.cwd()
EXPECTED_HASHES = {
    "artifacts/tables/main_results.csv": "EAB3478D19E04CAF97E07FC31FCD3CC36089C19320A64E96F7BAC9EB12D89921",
    "artifacts/stats/main_results.csv": "E40944BB6476D84E8C3FC65670B2DC5E7DB62CF47CA7FC6D0051768458CD0E32",
    "artifacts/cross_dataset/cross_dataset_results.csv": "8DA3E015146193FCD5D1F5F47A9E0A5ED84F55A4182B4BB5932DC657B8DAAD4C",
    "artifacts/runs/run_registry.jsonl": "A05A06FCA305CEDF2C46DBEAD17AC222A5F09E73AB105538479A049DF90A26CE",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def test_step10b_does_not_modify_historical_results() -> None:
    for relative_path, expected in EXPECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected


def test_step10b_does_not_claim_level3_completion_or_urd_win() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_readiness_report.json").read_text(encoding="utf-8"))
    text = (ROOT / "artifacts/reports/step10B_readiness_report.md").read_text(encoding="utf-8").casefold()

    assert report["level3_completed_artifact"] is False
    assert report["current_readiness"] != "LEVEL3_COMPLETED_ARTIFACT"
    assert "urd beats raw" not in text
    assert "ccf-b ready" not in text
