from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tokenization.validation import validate_tokenizer_manifest


def test_train_tokenizer_v2_generates_bpe_smoke_manifest(tmp_path: Path) -> None:
    output_dir = tmp_path / "bpe_smoke"
    manifest_path = output_dir / "tokenizer_manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/train_tokenizer_v2.py",
            "--tokenizer-type",
            "bpe",
            "--name",
            "bpe_smoke_unit",
            "--data",
            "artifacts/data_step2/wikitext2_smoke/train.jsonl",
            "--scope",
            "smoke",
            "--vocab-size",
            "128",
            "--seed",
            "42",
            "--output-dir",
            str(output_dir),
            "--manifest-output",
            str(manifest_path),
            "--allow-fallback",
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    assert "manifest_path" in result.stdout
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_tokenizer_manifest(manifest, Path.cwd())
    assert manifest["tokenizer_type"] == "lightweight_bpe_smoke"
    assert manifest["scope"] == "smoke"
    assert manifest["fallback_used"] is True
    assert manifest["level3_mainline"] is False
