from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.validation import validate_mechanism_manifest


def test_mechanism_config_requires_smoke_flag_for_smoke_scope() -> None:
    with pytest.raises(ValueError, match="smoke mechanism"):
        MechanismAnalysisConfig.from_mapping(
            {
                "analysis_name": "bad",
                "analysis_type": "proxy_utility",
                "scope": "smoke",
                "dataset_name": "dataset",
                "methods": ["method"],
                "smoke_only": False,
            }
        )


def test_repo_mechanism_manifest_schema_validates_proxy_output() -> None:
    path = Path("artifacts/analysis_step8/wikitext2_smoke/proxy_utility_urd_fixed/mechanism_manifest.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))

    validate_mechanism_manifest(manifest, Path.cwd())

    assert manifest["manifest_version"] == "step8.mechanism_manifest.v1"
    assert manifest["claim_allowed"] is False
    assert manifest["insufficient_evidence"] is True

