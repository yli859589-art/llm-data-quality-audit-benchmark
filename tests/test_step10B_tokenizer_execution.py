from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_tokenizer_report_does_not_promote_smoke_tokenizer() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_tokenizer_report.json").read_text(encoding="utf-8"))

    assert report["stage"] == "tokenizer"
    assert report["level3_tokenizer_ready"] is False
    assert report["completed"] is False
    assert report["smoke_only"] is False
    assert report["protocol_only"] is False

