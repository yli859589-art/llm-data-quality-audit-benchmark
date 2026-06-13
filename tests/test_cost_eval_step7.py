from __future__ import annotations

from pathlib import Path

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.cost_eval import run_cost_evaluation


def test_cost_evaluator_outputs_proxy_metrics(tmp_path: Path) -> None:
    config = EvaluationConfig.from_mapping(
        {
            "evaluation_name": "cost_unit",
            "evaluation_type": "cost",
            "scope": "smoke",
            "method_name": "urd_fixed",
            "dataset_name": "wikitext2_smoke",
            "filter_manifest_path": "artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json",
            "smoke_only": True,
        }
    )

    result = run_cost_evaluation(config, tmp_path / "cost", Path.cwd())

    assert result.metrics["compute_cost_proxy"] is True
    assert result.metrics["real_flops_available"] is False
    assert result.metrics["effectiveness_claim_allowed"] is False
