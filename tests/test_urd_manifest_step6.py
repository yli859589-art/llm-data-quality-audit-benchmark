from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "scripts"))

from scripts.check_urd_manifests import validate_urd_manifest


def test_repo_urd_manifests_validate() -> None:
    for path in Path("artifacts/filter_outputs_step6").glob("**/filter_manifest.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        validate_urd_manifest(manifest, Path.cwd())


def test_run_filter_v2_runs_urd_fixed_and_pareto(tmp_path: Path) -> None:
    for filter_name in ["urd_fixed", "urd_pareto"]:
        output_dir = tmp_path / filter_name
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_filter_v2.py",
                "--filter",
                filter_name,
                "--input",
                "artifacts/data_step2/wikitext2_smoke/train.jsonl",
                "--dataset-manifest",
                "artifacts/data_step2/wikitext2_smoke/data_manifest.json",
                "--tokenizer-manifest",
                "artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
                "--scope",
                "smoke",
                "--target-keep-rate",
                "0.5",
                "--seed",
                "42",
                "--output-dir",
                str(output_dir),
                "--allow-proxy",
            ],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        manifest = json.loads((output_dir / "filter_manifest.json").read_text(encoding="utf-8"))
        validate_urd_manifest(manifest, Path.cwd())
        assert payload["filter"] == filter_name
        assert payload["proxy_used"] is True
        assert payload["smoke_only"] is True
