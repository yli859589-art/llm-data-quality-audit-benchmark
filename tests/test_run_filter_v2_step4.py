from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from filters_v2.validation import validate_filter_manifest


def _run_filter(tmp_path: Path, filter_name: str, *extra: str) -> dict[str, object]:
    output_dir = tmp_path / filter_name
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_filter_v2.py",
            "--filter",
            filter_name,
            "--input",
            "artifacts/data_step2/wikitext2_smoke/train.jsonl",
            "--dataset-manifest",
            "artifacts/data_step2/wikitext2_smoke/data_manifest.json",
            "--tokenizer-manifest",
            "artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
            "--scope",
            "smoke",
            "--output-dir",
            str(output_dir),
            *extra,
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    manifest = json.loads((output_dir / "filter_manifest.json").read_text(encoding="utf-8"))
    validate_filter_manifest(manifest, Path.cwd())
    return payload


def test_run_filter_v2_can_run_raw_on_step2_smoke_data(tmp_path: Path) -> None:
    payload = _run_filter(tmp_path, "raw")

    assert payload["filter"] == "raw"
    assert payload["smoke_only"] is True
    assert payload["kept_docs"] == 3


def test_run_filter_v2_can_run_random_on_step2_smoke_data(tmp_path: Path) -> None:
    payload = _run_filter(
        tmp_path,
        "random_same_keep_rate",
        "--target-keep-rate",
        "0.5",
        "--seed",
        "42",
    )

    assert payload["filter"] == "random_same_keep_rate"
    assert payload["kept_docs"] == 2
