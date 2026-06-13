from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_release_manifest_declares_standalone_metadata_bundle() -> None:
    manifest = json.loads((ROOT / "artifacts/localmax_release/localmax_release_manifest.json").read_text(encoding="utf-8"))

    assert manifest["release_hotfix_version"] == "step10C_hotfix_v1"
    assert manifest["bundle_scope"] == "standalone_metadata_bundle"
    assert manifest["standalone_bundle"] is True
    assert manifest["raw_data_included"] is False
    assert manifest["binary_checkpoints_included"] is False
    assert manifest["metadata_and_metrics_included"] is True
    assert manifest["canonical_encoding"] == "UTF-8"
    assert manifest["canonical_newline"] == "LF"
    assert manifest["experimental_results_modified"] is False
    assert manifest["new_training_performed"] is False


def test_docs_and_readme_disclose_bundle_scope() -> None:
    for rel in ["README.md", "docs/LOCALMAX_RELEASE.md", "docs/LOCALMAX_REPRODUCIBILITY.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "Bundle scope: `standalone_metadata_bundle`" in text
        assert "raw data" in text.casefold()
        assert "binary checkpoints" in text.casefold()

