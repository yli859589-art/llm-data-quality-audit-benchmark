from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.scale_trend import run_scale_trend_analysis


def test_scale_trend_marks_medium_and_large_lite_unavailable(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "scale",
            "analysis_type": "scale_trend",
            "scope": "main_protocol",
            "dataset_name": "wikitext2_smoke",
            "methods": ["protocol_only"],
            "protocol_only": True,
        }
    )

    result = run_scale_trend_analysis(config, tmp_path, Path.cwd())

    assert result.summary["medium_or_large_lite_completed"] is False
    assert result.insufficient_evidence is True

