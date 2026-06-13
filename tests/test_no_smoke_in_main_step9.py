from __future__ import annotations

from pathlib import Path

from artifacts_v2.table_linker import MAIN_TABLES, smoke_or_protocol_in_main_tables


ROOT = Path.cwd()


def test_smoke_and_step_artifact_paths_do_not_enter_main_tables() -> None:
    assert smoke_or_protocol_in_main_tables(ROOT) == []


def test_main_tables_exist_as_historical_tables() -> None:
    for table in MAIN_TABLES:
        assert (ROOT / table).exists()
