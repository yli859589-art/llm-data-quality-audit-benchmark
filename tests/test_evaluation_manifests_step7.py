from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from evaluation_v2.validation import validate_evaluation_manifest


def test_repo_evaluation_manifests_validate() -> None:
    for path in Path("artifacts/evaluation_step7").glob("**/evaluation_manifest.json"):
        validate_evaluation_manifest(json.loads(path.read_text(encoding="utf-8")), Path.cwd())


def test_evaluate_all_v2_can_run_lm_risk_and_pareto_smoke(tmp_path: Path) -> None:
    commands = [
        [
            "--evaluation",
            "lm",
            "--training-manifest",
            "artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json",
            "--method-name",
            "bpe_tiny_smoke",
            "--output-dir",
            str(tmp_path / "lm"),
        ],
        [
            "--evaluation",
            "risk",
            "--filter-manifest",
            "artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json",
            "--method-name",
            "urd_fixed",
            "--output-dir",
            str(tmp_path / "risk"),
        ],
        [
            "--evaluation",
            "pareto",
            "--filter-manifest",
            "artifacts/filter_outputs_step6/wikitext2_smoke/urd_pareto/filter_manifest.json",
            "--method-name",
            "urd_pareto",
            "--output-dir",
            str(tmp_path / "pareto"),
        ],
    ]
    for command in commands:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/evaluate_all_v2.py",
                *command,
                "--dataset-name",
                "wikitext2_smoke",
                "--scope",
                "smoke",
                "--allow-smoke",
            ],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        assert payload["effectiveness_claim_allowed"] is False
