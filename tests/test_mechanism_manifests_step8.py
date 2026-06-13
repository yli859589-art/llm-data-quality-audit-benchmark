from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from analysis_v2.validation import validate_mechanism_manifest


def test_repo_mechanism_manifests_validate() -> None:
    manifests = list(Path("artifacts/analysis_step8").glob("**/mechanism_manifest.json"))
    assert len(manifests) >= 9
    for path in manifests:
        validate_mechanism_manifest(json.loads(path.read_text(encoding="utf-8")), Path.cwd())


def test_run_mechanism_analysis_v2_can_run_proxy_overfiltering_and_pareto_smoke(tmp_path: Path) -> None:
    commands = [
        [
            "--analysis",
            "proxy_utility",
            "--method-name",
            "urd_fixed",
            "--filter-manifest",
            "artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json",
            "--evaluation-manifest",
            "artifacts/evaluation_step7/wikitext2_smoke/lm_bpe_tiny/evaluation_manifest.json",
            "--output-dir",
            str(tmp_path / "proxy"),
        ],
        [
            "--analysis",
            "overfiltering",
            "--method-name",
            "urd_fixed",
            "--filter-manifest",
            "artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json",
            "--output-dir",
            str(tmp_path / "over"),
        ],
        [
            "--analysis",
            "pareto_mechanism",
            "--method-name",
            "urd_pareto",
            "--filter-manifest",
            "artifacts/filter_outputs_step6/wikitext2_smoke/urd_pareto/filter_manifest.json",
            "--output-dir",
            str(tmp_path / "pareto"),
        ],
    ]
    for command in commands:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_mechanism_analysis_v2.py",
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
        assert payload["claim_allowed"] is False
        assert payload["insufficient_evidence"] is True

