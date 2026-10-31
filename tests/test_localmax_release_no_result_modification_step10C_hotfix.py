from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path.cwd()
PROTECTED = {
    "artifacts/tables/main_results.csv": "D8E593744EEB95CECB422C600CEC89C70279B28E09FCD3DE96AA8D1C9F2A7C3F",
    "artifacts/stats/main_results.csv": "38AA59CE82B2511FBF711D4B696E7B47C7C89F94D2ABCA0835D75AC0F14057B4",
    "artifacts/cross_dataset/cross_dataset_results.csv": "5003F1534231EEDAEE6B501D6F9769C45CEF749CFE37921E8AB10CCE12C73A86",
    "artifacts/runs/run_registry.jsonl": "D9EF6C857EC44CEF1659F1444752C6B4FC2C86C443F27665621CEA39B45086D8",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest().upper()


def test_protected_historical_results_are_unchanged() -> None:
    for rel, digest in PROTECTED.items():
        assert _sha(ROOT / rel) == digest


def test_localmax_release_values_match_source_table() -> None:
    source = list(
        csv.DictReader(
            (ROOT / "artifacts/localmax_tables/localmax_main_results.csv").open(encoding="utf-8")
        )
    )
    release = list(
        csv.DictReader(
            (ROOT / "artifacts/localmax_release/tables/localmax_main_results_release.csv").open(
                encoding="utf-8"
            )
        )
    )

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
