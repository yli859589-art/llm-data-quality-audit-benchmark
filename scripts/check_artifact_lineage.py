from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from pathlib import Path

from experiment_utils import root
from registry_utils import file_hash, read_registry_jsonl


def _is_superseded_data_manifest(row: dict[str, str], rows: list[dict[str, str]]) -> bool:
    artifact_path = row.get("artifact_path", "").replace("\\", "/")
    if row.get("baseline_name") != "data_prepare":
        return False
    if not artifact_path.endswith("/data_manifest.json"):
        return False
    row_timestamp = str(row.get("timestamp_utc", ""))
    return any(
        other.get("baseline_name") == "data_prepare"
        and other.get("dataset_key") == row.get("dataset_key")
        and str(other.get("timestamp_utc", "")) > row_timestamp
        for other in rows
    )


def _is_superseded_same_artifact(row: dict[str, str], rows: list[dict[str, str]]) -> bool:
    artifact_path = row.get("artifact_path", "").replace("\\", "/")
    if not artifact_path:
        return False
    row_timestamp = str(row.get("timestamp_utc", ""))
    return any(
        other.get("artifact_path", "").replace("\\", "/") == artifact_path
        and str(other.get("timestamp_utc", "")) > row_timestamp
        for other in rows
    )


def main() -> None:
    rows = read_registry_jsonl()
    errors = []
    superseded = 0
    for row in rows:
        artifact_path = row.get("artifact_path", "")
        if not artifact_path:
            if row["run_status"].startswith("failed"):
                continue
            errors.append(f"{row['run_id']} missing artifact_path")
            continue
        path = root / Path(artifact_path)
        if not path.exists():
            errors.append(f"{row['run_id']} artifact missing: {artifact_path}")
            continue
        expected = row.get("artifact_hash", "")
        if expected and file_hash(path) != expected:
            if _is_superseded_data_manifest(row, rows) or _is_superseded_same_artifact(
                row,
                rows,
            ):
                superseded += 1
                continue
            errors.append(f"{row['run_id']} artifact hash mismatch")
    if errors:
        raise SystemExit("Artifact lineage check failed." + "\n" + "\n".join(errors))
    print(f"Artifact lineage check: ok ({len(rows)} rows, {superseded} superseded)")


if __name__ == "__main__":
    main()
