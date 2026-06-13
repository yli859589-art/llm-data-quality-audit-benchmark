from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.overfiltering import run_overfiltering_analysis


def test_overfiltering_outputs_keep_rate_diagnostics(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "over",
            "analysis_type": "overfiltering",
            "scope": "smoke",
            "dataset_name": "wikitext2_smoke",
            "methods": ["urd_fixed"],
            "filter_manifest_paths": ["artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json"],
            "smoke_only": True,
        }
    )

    result = run_overfiltering_analysis(config, tmp_path, Path.cwd())

    assert result.summary["document_keep_rate"] is not None
    assert result.insufficient_evidence is True
    assert (tmp_path / "overfiltering_diagnostics.csv").exists()

