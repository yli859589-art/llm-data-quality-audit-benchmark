from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_level3_artifact_paths_are_relative_and_isolated() -> None:
    payload = json.loads((ROOT / "configs/level3/artifact_paths.yaml").read_text(encoding="utf-8"))
    values = list(payload["artifact_roots"].values()) + list(payload["named_outputs"].values())

    assert all(not Path(value).is_absolute() for value in values)
    assert all(value.startswith("artifacts/level3_") or value == "artifacts/claim_map/claim_map_level3.json" for value in values)
    assert payload["named_outputs"]["main_table"] == "artifacts/level3_tables/main_results_level3.csv"
    assert payload["named_outputs"]["final_release_zip"] == "artifacts/level3_release/level3_release_candidate.zip"


def test_level3_paths_do_not_replace_historical_main_results() -> None:
    payload = json.loads((ROOT / "configs/level3/artifact_paths.yaml").read_text(encoding="utf-8"))
    named_outputs = set(payload["named_outputs"].values())

    assert "artifacts/tables/main_results.csv" not in named_outputs
    assert "artifacts/stats/main_results.csv" not in named_outputs
    assert "artifacts/cross_dataset/cross_dataset_results.csv" not in named_outputs

