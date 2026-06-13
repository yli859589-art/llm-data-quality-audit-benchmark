from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.validation import validate_evaluation_manifest


def test_evaluation_config_requires_smoke_flag_for_smoke_scope() -> None:
    with pytest.raises(ValueError, match="smoke evaluation"):
        EvaluationConfig.from_mapping(
            {
                "evaluation_name": "bad",
                "evaluation_type": "lm",
                "scope": "smoke",
                "method_name": "method",
                "dataset_name": "dataset",
                "smoke_only": False,
            }
        )


def test_evaluation_manifest_schema_validates_repo_lm_output() -> None:
    manifest = json.loads(
        Path("artifacts/evaluation_step7/wikitext2_smoke/lm_bpe_tiny/evaluation_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    validate_evaluation_manifest(manifest, Path.cwd())

    assert manifest["manifest_version"] == "step7.evaluation_manifest.v1"
    assert manifest["effectiveness_claim_allowed"] is False
