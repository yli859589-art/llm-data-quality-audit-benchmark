from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from data_sources.validation import validate_manifest


def test_prepare_data_v2_generates_wikitext2_smoke_jsonl_and_manifest(tmp_path: Path) -> None:
    output = tmp_path / "train.jsonl"
    manifest_path = tmp_path / "data_manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/prepare_data_v2.py",
            "--dataset",
            "wikitext2",
            "--split",
            "train",
            "--scope",
            "smoke",
            "--token-budget",
            "10K",
            "--seed",
            "42",
            "--output",
            str(output),
            "--manifest-output",
            str(manifest_path),
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "manifest_path" in result.stdout
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows
    for row in rows:
        assert {"doc_id", "text", "source", "split", "metadata"}.issubset(row)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(manifest, Path.cwd())
    assert manifest["scope"] == "smoke"
    assert manifest["smoke_only"] is True
