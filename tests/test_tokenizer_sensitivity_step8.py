from __future__ import annotations

from pathlib import Path

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.tokenizer_sensitivity import run_tokenizer_sensitivity_analysis


def test_tokenizer_sensitivity_marks_formal_bpe_matrix_unavailable(tmp_path: Path) -> None:
    config = MechanismAnalysisConfig.from_mapping(
        {
            "analysis_name": "tok",
            "analysis_type": "tokenizer_sensitivity",
            "scope": "main_protocol",
            "dataset_name": "wikitext2_smoke",
            "methods": ["protocol_only"],
            "protocol_only": True,
        }
    )

    result = run_tokenizer_sensitivity_analysis(config, tmp_path, Path.cwd())

    assert result.summary["formal_tokenizer_matrix_completed"] is False
    assert result.insufficient_evidence is True

