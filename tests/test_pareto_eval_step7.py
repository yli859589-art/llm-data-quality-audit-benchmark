from __future__ import annotations

from pathlib import Path

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.pareto import run_pareto_evaluation


def test_pareto_evaluator_reads_step6_pareto_artifacts(tmp_path: Path) -> None:
    config = EvaluationConfig.from_mapping(
        {
            "evaluation_name": "pareto_unit",
            "evaluation_type": "pareto",
            "scope": "smoke",
            "method_name": "urd_pareto",
            "dataset_name": "wikitext2_smoke",
            "filter_manifest_path": "artifacts/filter_outputs_step6/wikitext2_smoke/urd_pareto/filter_manifest.json",
            "smoke_only": True,
        }
    )

    result = run_pareto_evaluation(config, tmp_path / "pareto", Path.cwd())

    assert result.metrics["component_score_rows"] > 0
    assert result.metrics["pareto_improvement_claim_allowed"] is False
    assert (tmp_path / "pareto" / "pareto_frontier_summary.csv").exists()
