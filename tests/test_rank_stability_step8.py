from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.rank_stability import run_rank_stability_analysis


def test_rank_stability_protocol_returns_insufficient_evidence(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "rank",
            "analysis_type": "rank_stability",
            "scope": "main_protocol",
            "dataset_name": "wikitext2_smoke",
            "methods": ["protocol_only"],
            "protocol_only": True,
        }
    )

    result = run_rank_stability_analysis(config, tmp_path, Path.cwd())

    assert result.evidence_sufficiency == "protocol_only"
    assert result.insufficient_evidence is True
    assert result.claim_allowed is False

