from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_protocol_artifacts_are_not_marked_completed() -> None:
    offenders = []
    for path in sorted((ROOT / "artifacts").glob("**/*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("protocol_only") is True and payload.get("completed") is True:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_downstream_protocol_is_not_completed_evidence() -> None:
    manifest = ROOT / "artifacts/evaluation_step7/downstream_protocol/evaluation_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert payload.get("protocol_only") is True
    assert payload.get("completed") is not True
