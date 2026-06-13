from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "artifacts" / "dataaudit_lm" / "reports"
INTEGRITY = ROOT / "artifacts" / "dataaudit_lm" / "integrity"
TABLES = ROOT / "artifacts" / "dataaudit_lm" / "tables"
FIGURES = ROOT / "artifacts" / "dataaudit_lm" / "figures"


def ensure_public_artifact_dirs() -> None:
    for path in [REPORTS, INTEGRITY, TABLES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)
