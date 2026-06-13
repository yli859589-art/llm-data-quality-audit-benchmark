from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.failure_taxonomy import run_failure_taxonomy_analysis


def test_failure_taxonomy_includes_hdqspp_failure_and_negative_result_preservation(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "failures",
            "analysis_type": "failure_taxonomy",
            "scope": "smoke",
            "dataset_name": "wikitext2_smoke",
            "methods": ["all_methods"],
            "smoke_only": True,
        }
    )

    result = run_failure_taxonomy_analysis(config, tmp_path, Path.cwd())
    text = (tmp_path / "failure_taxonomy.md").read_text(encoding="utf-8")

    assert result.summary["hdqspp_historical_failure_recorded"] is True
    assert "HDQS++ v3 did not outperform raw" in text
    assert result.claim_allowed is False

