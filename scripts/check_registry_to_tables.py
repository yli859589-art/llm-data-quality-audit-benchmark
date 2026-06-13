from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from artifacts_v2.registry import read_registry
from artifacts_v2.table_linker import main_tables_have_registry_records, smoke_or_protocol_in_main_tables
from experiment_utils import root


def main() -> None:
    registry_path = root / "artifacts" / "registry_v2" / "artifact_registry.jsonl"
    rows = read_registry(registry_path)
    errors = []
    errors.extend(main_tables_have_registry_records(rows, root))
    errors.extend(smoke_or_protocol_in_main_tables(root))
    main_records = [row for row in rows if row.get("artifact_type") == "main_table"]
    for row in main_records:
        if row.get("notes") != "historical_legacy=true":
            errors.append(f"main table registry record must be historical_legacy=true: {row.get('path')}")
    if errors:
        raise SystemExit("Registry-to-table consistency check failed.\n" + "\n".join(errors))
    print(f"Registry-to-table consistency check: ok ({len(main_records)} main table records)")


if __name__ == "__main__":
    main()

