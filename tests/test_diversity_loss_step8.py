from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.diversity_loss import run_diversity_loss_analysis


def test_diversity_loss_marks_source_and_embedding_gaps(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "diversity",
            "analysis_type": "diversity_loss",
            "scope": "smoke",
            "dataset_name": "wikitext2_smoke",
            "methods": ["urd_fixed"],
            "filter_manifest_paths": ["artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json"],
            "smoke_only": True,
        }
    )

    result = run_diversity_loss_analysis(config, tmp_path, Path.cwd())

    assert result.summary["semantic_embedding_unavailable"] is True
    assert result.insufficient_evidence is True

