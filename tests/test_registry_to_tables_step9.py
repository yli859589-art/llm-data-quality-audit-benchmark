from __future__ import annotations

from pathlib import Path

from artifacts_v2.registry import read_registry
from artifacts_v2.table_linker import main_tables_have_registry_records, smoke_or_protocol_in_main_tables


ROOT = Path.cwd()


def test_registry_has_records_for_all_historical_main_tables() -> None:
    rows = read_registry(ROOT / "artifacts/registry_v2/artifact_registry.jsonl")

    assert main_tables_have_registry_records(rows, ROOT) == []


def test_registry_marks_main_tables_historical_not_level3() -> None:
    rows = read_registry(ROOT / "artifacts/registry_v2/artifact_registry.jsonl")
    main_rows = [row for row in rows if row.get("artifact_type") == "main_table"]

    assert len(main_rows) == 3
    assert all(row.get("main_evidence") is True for row in main_rows)
    assert all(row.get("level3_evidence") is False for row in main_rows)
    assert all(row.get("notes") == "historical_legacy=true" for row in main_rows)
    assert smoke_or_protocol_in_main_tables(ROOT) == []
