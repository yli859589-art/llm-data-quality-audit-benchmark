from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from registry_utils import (
    ALLOWED_DATASET_SCOPE,
    ALLOWED_DATASET_STATUS,
    ALLOWED_RUN_STATUS,
    REGISTRY_FIELDS,
    read_registry_jsonl,
    rebuild_registry_csv,
)


def main() -> None:
    rows = read_registry_jsonl()
    if not rows:
        raise SystemExit("run_registry.jsonl has no rows")
    seen = set()
    errors = []
    for index, row in enumerate(rows, start=1):
        missing = [field for field in REGISTRY_FIELDS if field not in row]
        if missing:
            errors.append(f"row {index} missing fields: {missing}")
        if row["run_id"] in seen:
            errors.append(f"duplicate run_id: {row['run_id']}")
        seen.add(row["run_id"])
        if row["run_status"] not in ALLOWED_RUN_STATUS:
            errors.append(f"invalid run_status for {row['run_id']}: {row['run_status']}")
        if row["dataset_status"] not in ALLOWED_DATASET_STATUS:
            errors.append(
                f"invalid dataset_status for {row['run_id']}: {row['dataset_status']}"
            )
        if row["dataset_scope"] not in ALLOWED_DATASET_SCOPE:
            errors.append(f"invalid dataset_scope for {row['run_id']}: {row['dataset_scope']}")
    if errors:
        raise SystemExit("Registry schema check failed." + "\n" + "\n".join(errors))
    rebuild_registry_csv()
    print(f"Registry schema check: ok ({len(rows)} rows)")


if __name__ == "__main__":
    main()
