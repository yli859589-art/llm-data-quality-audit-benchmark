from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path.cwd()
PROTECTED = {
    "artifacts/tables/main_results.csv": "EAB3478D19E04CAF97E07FC31FCD3CC36089C19320A64E96F7BAC9EB12D89921",
    "artifacts/stats/main_results.csv": "E40944BB6476D84E8C3FC65670B2DC5E7DB62CF47CA7FC6D0051768458CD0E32",
    "artifacts/cross_dataset/cross_dataset_results.csv": "8DA3E015146193FCD5D1F5F47A9E0A5ED84F55A4182B4BB5932DC657B8DAAD4C",
    "artifacts/runs/run_registry.jsonl": "A05A06FCA305CEDF2C46DBEAD17AC222A5F09E73AB105538479A049DF90A26CE",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_protected_historical_results_are_unchanged() -> None:
    for rel, digest in PROTECTED.items():
        assert _sha(ROOT / rel) == digest


def test_localmax_release_values_match_source_table() -> None:
    source = list(csv.DictReader((ROOT / "artifacts/localmax_tables/localmax_main_results.csv").open(encoding="utf-8")))
    release = list(csv.DictReader((ROOT / "artifacts/localmax_release/tables/localmax_main_results_release.csv").open(encoding="utf-8")))

    assert len(source) == len(release) == 24
    value_fields = [
        "dataset",
        "method",
        "seed",
        "model_scale",
        "steps_completed",
        "tokens_seen",
        "valid_loss",
        "valid_ppl_clipped",
        "ppl_clipped",
        "ppl_comparable",
        "metric_for_comparison",
        "evidence_level",
    ]
    for source_row, release_row in zip(source, release, strict=True):
        for field in value_fields:
            assert release_row[field] == source_row[field]
        assert release_row["training_manifest"].startswith("artifacts/localmax_release/")
        assert release_row["evaluation_manifest"].startswith("artifacts/localmax_release/")

