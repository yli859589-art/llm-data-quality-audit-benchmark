from __future__ import annotations

from pathlib import Path


MAIN_TABLES = [
    "artifacts/tables/main_results.csv",
    "artifacts/stats/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
]


def main_tables_have_registry_records(rows: list[dict], root: Path) -> list[str]:
    paths = {str(row.get("path", "")) for row in rows}
    errors = []
    for table in MAIN_TABLES:
        if not (root / table).exists():
            errors.append(f"main table missing: {table}")
        elif table not in paths:
            errors.append(f"main table missing registry record: {table}")
    return errors


def smoke_or_protocol_in_main_tables(root: Path) -> list[str]:
    tokens = ["smoke", "protocol_only", "analysis_step8", "evaluation_step7", "training_step5", "filter_outputs_step6"]
    errors = []
    for table in MAIN_TABLES:
        path = root / table
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        for token in tokens:
            if token.casefold() in text:
                errors.append(f"{table} contains non-main token: {token}")
    return errors

