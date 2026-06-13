from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tokenization.manifest import sha256_file


def append_training_registry(root: Path, manifest: dict[str, Any]) -> None:
    registry_path = root / "artifacts" / "training_step5" / "training_registry.jsonl"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(str(manifest.get("metrics_path", ""))).parent / "training_manifest.json"
    resolved_manifest = root / manifest_path if not manifest_path.is_absolute() else manifest_path
    run_id = f"{manifest['experiment_name']}::{manifest['scope']}::seed{manifest['seed']}"
    row = {
        "run_id": run_id,
        "experiment_name": manifest["experiment_name"],
        "scope": manifest["scope"],
        "smoke_only": manifest["smoke_only"],
        "completed": manifest["completed"],
        "implemented_but_not_run": manifest["implemented_but_not_run"],
        "created_at": manifest.get("created_at", datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
        "manifest_path": manifest_path.as_posix(),
        "manifest_hash": sha256_file(resolved_manifest) if resolved_manifest.exists() else "",
        "metrics_path": manifest["metrics_path"],
        "checkpoint_path": manifest["checkpoint_path"],
        "notes": "Step 5 registry is smoke/protocol only and does not write artifacts/runs/run_registry.jsonl.",
    }
    rows: list[dict[str, Any]] = []
    if registry_path.exists():
        for line in registry_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    rows = [existing for existing in rows if existing.get("run_id") != run_id]
    rows.append(row)
    with registry_path.open("w", encoding="utf-8") as handle:
        for existing in rows:
            handle.write(json.dumps(existing, sort_keys=True) + "\n")
