from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path.cwd()


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        canonical = data
    else:
        canonical = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper()


def _sha256_variants(path: Path) -> set[str]:
    data = path.read_bytes()
    variants = {hashlib.sha256(data).hexdigest().upper()}
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return variants
    normalized_lf = text.replace("\r\n", "\n").replace("\r", "\n")
    variants.add(hashlib.sha256(normalized_lf.encode("utf-8")).hexdigest().upper())
    variants.add(hashlib.sha256(normalized_lf.replace("\n", "\r\n").encode("utf-8")).hexdigest().upper())
    return variants


def test_localmax_release_manifest_and_hashes_exist() -> None:
    manifest = json.loads((ROOT / "artifacts/localmax_release/localmax_release_manifest.json").read_text(encoding="utf-8"))
    hashes = json.loads((ROOT / "artifacts/localmax_release/localmax_hashes.json").read_text(encoding="utf-8"))

    assert manifest["current_readiness"] == "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
    assert manifest["level3_completed_artifact"] is False
    assert manifest["historical_results_modified"] is False
    assert manifest["training_manifest_links"]
    assert manifest["evaluation_manifest_links"]
    assert manifest["data_manifest_links"]
    assert "hashes" in hashes


def test_localmax_release_registry_hashes_are_valid() -> None:
    registry = ROOT / "artifacts/localmax_release/localmax_artifact_registry.jsonl"
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert rows
    assert any(row["path"] == "artifacts/localmax_release/tables/localmax_main_results_release.csv" for row in rows)
    assert any(row["path"] == "docs/LOCALMAX_RESULTS.md" for row in rows)
    for row in rows:
        path = ROOT / row["path"]
        assert path.exists(), row["path"]
        assert row["sha256"] in _sha256_variants(path)
        assert row["level3_completed_artifact"] is False
