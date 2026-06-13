from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.proxy_utility import run_proxy_utility_analysis


def test_proxy_utility_outputs_insufficient_evidence_without_per_doc_target(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "proxy",
            "analysis_type": "proxy_utility",
            "scope": "smoke",
            "dataset_name": "wikitext2_smoke",
            "methods": ["urd_fixed"],
            "filter_manifest_paths": ["artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json"],
            "evaluation_manifest_paths": ["artifacts/evaluation_step7/wikitext2_smoke/lm_bpe_tiny/evaluation_manifest.json"],
            "smoke_only": True,
        }
    )

    result = run_proxy_utility_analysis(config, tmp_path, Path.cwd())

    assert result.insufficient_evidence is True
    assert result.claim_allowed is False
    assert "no_per_document_utility_target" in (tmp_path / "proxy_utility_diagnostics.csv").read_text(
        encoding="utf-8"
    )

