from __future__ import annotations


def lineage_warnings(rows: list[dict]) -> list[str]:
    warnings = []
    for row in rows:
        if row.get("main_evidence") and not row.get("parent_artifacts") and row.get("artifact_type") == "main_table":
            warnings.append(f"{row.get('path')} is historical_legacy=true; no fake lineage was created.")
    return warnings

