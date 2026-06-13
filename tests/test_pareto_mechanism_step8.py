from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.pareto_mechanism import run_pareto_mechanism_analysis


def test_pareto_mechanism_does_not_claim_improvement(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "pareto",
            "analysis_type": "pareto_mechanism",
            "scope": "smoke",
            "dataset_name": "wikitext2_smoke",
            "methods": ["urd_pareto"],
            "filter_manifest_paths": ["artifacts/filter_outputs_step6/wikitext2_smoke/urd_pareto/filter_manifest.json"],
            "smoke_only": True,
        }
    )

    result = run_pareto_mechanism_analysis(config, tmp_path, Path.cwd())

    assert result.summary["pareto_improvement_claim_allowed"] is False
    assert result.insufficient_evidence is True

