from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_tokenizer_is_gpt2_mainline_not_smoke() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_tokenizer_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json").read_text(encoding="utf-8"))

    assert report["localmax_tokenizer_ready"] is True
    assert manifest["tokenizer_type"] == "gpt2_bpe"
    assert manifest["actual_gpt2_tokenizer_loaded"] is True
    assert manifest["char_level_mainline"] is False
    assert manifest["lightweight_bpe_smoke_mainline"] is False

