from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from artifacts_v2.registry import read_registry
from experiment_utils import root


def main() -> None:
    rows = read_registry(root / "artifacts" / "registry_v2" / "artifact_registry.jsonl")
    paths = {row.get("path"): row for row in rows}
    required = [
        "artifacts/tables/main_results.csv",
        "artifacts/stats/main_results.csv",
        "artifacts/cross_dataset/cross_dataset_results.csv",
    ]
    errors = []
    for path in required:
        row = paths.get(path)
        if row is None:
            errors.append(f"missing registry record for {path}")
            continue
        if row.get("main_evidence") is not True:
            errors.append(f"{path} must remain a main_evidence historical table")
        if row.get("level3_evidence") is not False:
            errors.append(f"{path} must not be level3_evidence")
        if row.get("evidence_level") != "historical_main_only":
            errors.append(f"{path} must be historical_main_only")
    if errors:
        raise SystemExit("Main-results-from-registry check failed.\n" + "\n".join(errors))
    print("Main-results-from-registry check: ok")


if __name__ == "__main__":
    main()

