from __future__ import annotations

from pathlib import Path

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.lm_metrics import run_lm_evaluation


def test_lm_smoke_evaluator_reads_step5_training_manifest(tmp_path: Path) -> None:
    config = EvaluationConfig.from_mapping(
        {
            "evaluation_name": "lm_unit",
            "evaluation_type": "lm",
            "scope": "smoke",
            "method_name": "bpe_tiny_smoke",
            "dataset_name": "wikitext2_smoke",
            "training_manifest_path": "artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json",
            "smoke_only": True,
        }
    )

    result = run_lm_evaluation(config, tmp_path / "lm", Path.cwd())

    assert result.smoke_only is True
    assert result.metrics["validation_ppl"] is not None
    assert result.metrics["main_evidence"] is False
    assert (tmp_path / "lm" / "evaluation_manifest.json").exists()
