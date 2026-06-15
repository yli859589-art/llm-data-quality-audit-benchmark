from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


def test_localmax_v2_release_registry_hashes_are_real() -> None:
    registry = ROOT / "artifacts/localmax_v2_release/localmax_v2_artifact_registry.jsonl"
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    for row in rows:
        path = ROOT / row["path"]
        assert path.exists()
        assert row["sha256"] in _sha256_variants(path)
        assert path.stat().st_size == row["size_bytes"]
