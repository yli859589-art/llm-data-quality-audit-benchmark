from __future__ import annotations

from pathlib import Path

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.risk_eval import run_risk_evaluation


def test_risk_evaluator_outputs_proxy_metrics(tmp_path: Path) -> None:
    config = EvaluationConfig.from_mapping(
        {
            "evaluation_name": "risk_unit",
            "evaluation_type": "risk",
            "scope": "smoke",
            "method_name": "urd_fixed",
            "dataset_name": "wikitext2_smoke",
            "filter_manifest_path": "artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json",
            "smoke_only": True,
        }
    )

    result = run_risk_evaluation(config, tmp_path / "risk", Path.cwd())

    assert result.metrics["proxy_metric"] is True
    assert result.metrics["toxicity_classifier"] == "unavailable"
    assert result.metrics["effectiveness_claim_allowed"] is False
