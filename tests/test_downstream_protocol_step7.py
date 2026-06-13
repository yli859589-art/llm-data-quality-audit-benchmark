from __future__ import annotations

from pathlib import Path

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.downstream import run_downstream_protocol


def test_downstream_protocol_does_not_claim_completed(tmp_path: Path) -> None:
    config = EvaluationConfig.from_mapping(
        {
            "evaluation_name": "downstream_protocol_unit",
            "evaluation_type": "downstream_protocol",
            "scope": "main_protocol",
            "method_name": "protocol_only",
            "dataset_name": "wikitext2_smoke",
            "protocol_only": True,
        }
    )

    result = run_downstream_protocol(config, tmp_path / "downstream", Path.cwd())

    assert result.protocol_only is True
    assert result.completed is False
    assert result.metrics["official_downstream_completed"] is False
    assert result.metrics["effectiveness_claim_allowed"] is False
