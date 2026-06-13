from __future__ import annotations

from pathlib import Path

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.stability import run_stability_evaluation
from evaluation_v2.statistics import bootstrap_ci


def test_stability_evaluator_reports_insufficient_evidence(tmp_path: Path) -> None:
    config = EvaluationConfig.from_mapping(
        {
            "evaluation_name": "stability_unit",
            "evaluation_type": "stability",
            "scope": "main_protocol",
            "method_name": "protocol_only",
            "dataset_name": "wikitext2_smoke",
            "protocol_only": True,
        }
    )

    result = run_stability_evaluation(config, tmp_path / "stability", Path.cwd())

    assert result.metrics["insufficient_evidence"] is True
    assert result.metrics["ranking_stability_claim_allowed"] is False


def test_bootstrap_ci_warns_for_single_sample() -> None:
    ci = bootstrap_ci([1.0])

    assert ci["warning"] == "insufficient_sample_size_for_bootstrap"
    assert ci["ci95_low"] is None
