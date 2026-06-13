from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.domain_shift import run_domain_shift_analysis


def test_domain_shift_outputs_shift_diagnostics_or_unavailable_flags(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "shift",
            "analysis_type": "domain_shift",
            "scope": "smoke",
            "dataset_name": "wikitext2_smoke",
            "methods": ["urd_fixed"],
            "filter_manifest_paths": ["artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json"],
            "smoke_only": True,
        }
    )

    result = run_domain_shift_analysis(config, tmp_path, Path.cwd())

    assert result.summary["source_domain_shift_unavailable"] is True
    assert result.insufficient_evidence is True

