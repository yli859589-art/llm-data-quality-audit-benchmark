from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_release_registry_hashes_are_real() -> None:
    registry = ROOT / "artifacts/localmax_v2_release/localmax_v2_artifact_registry.jsonl"
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    for row in rows:
        path = ROOT / row["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == row["sha256"]
        assert path.stat().st_size == row["size_bytes"]
