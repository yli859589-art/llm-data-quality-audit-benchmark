from __future__ import annotations

from pathlib import Path

from readiness_v2.gates import (
    claim_gate,
    data_gate,
    model_scale_gate,
    scan_forbidden_claims,
    tokenizer_gate,
)


ROOT = Path.cwd()


def test_level3_gate_statuses_match_current_evidence_boundary() -> None:
    assert data_gate(ROOT).status == "not_ready"
    assert tokenizer_gate(ROOT).status == "partial"
    assert model_scale_gate(ROOT).status == "partial"
    assert claim_gate(ROOT).status == "pass"


def test_claim_gate_detects_forbidden_promotional_claim(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("URD-Selector beats raw on full C4.\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()

    findings = scan_forbidden_claims(tmp_path)

    assert findings
    assert any("beats raw" in item["text"] for item in findings)


def test_claim_gate_allows_forbidden_phrase_in_negative_boundary_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "This repository does not claim URD-Selector beats raw and is not CCF-B ready.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()

    assert scan_forbidden_claims(tmp_path) == []
