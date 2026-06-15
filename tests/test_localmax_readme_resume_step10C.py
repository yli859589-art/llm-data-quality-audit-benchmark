from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd()


def test_localmax_release_docs_report_legacy_state_without_overclaiming() -> None:
    text = (ROOT / "docs/LOCALMAX_RELEASE.md").read_text(encoding="utf-8")

    assert "Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`" in text
    assert "Level 3 status: `not completed`" in text
    assert "valid_loss" in text
    assert "clipped and not comparable" in text
    assert "LOCAL_MAX_LEVEL2_5_COMPLETED" not in text
    assert "LEVEL3_COMPLETED_ARTIFACT" not in text
    assert "URD beats raw" not in text
    assert "SOTA" not in text


def test_readme_now_uses_dataaudit_lm_identity() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "DataAudit-LM" in text
    assert "reproducible research artifact" in text
    assert "Planned final matrix" in text
    assert "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED" not in text


def test_resume_bullets_are_honest_and_specific() -> None:
    text = (ROOT / "RESUME_BULLETS.md").read_text(encoding="utf-8")

    assert "two 20M-token corpora" in text
    assert "24 strengthened small-model training runs" in text
    assert "claim hygiene safeguards" in text
    forbidden = ["SOTA", "CCF-B ready", "weak CCF-A achieved", "Proved URD outperforms raw"]
    for phrase in forbidden:
        assert phrase not in text
