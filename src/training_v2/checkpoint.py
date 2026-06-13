from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from torch import nn

from tokenization.manifest import sha256_file


def project_relative(path: str | Path, root: Path) -> str:
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def save_checkpoint(
    *,
    model: nn.Module,
    output_dir: Path,
    root: Path,
    payload: dict[str, Any],
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {
            "checkpoint_path": "",
            "checkpoint_hash": "",
            "checkpoint_manifest_path": "",
            "checkpoint_manifest_hash": "",
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.pt"
    torch.save({"model_state_dict": model.state_dict(), **payload}, checkpoint_path)
    checkpoint_hash = sha256_file(checkpoint_path)
    manifest = {
        "manifest_version": "step5.checkpoint_manifest.v1",
        "checkpoint_path": project_relative(checkpoint_path, root),
        "checkpoint_hash": checkpoint_hash,
        "model_name": payload.get("model_config", {}).get("model_name", ""),
        "parameter_count": payload.get("model_config", {}).get("parameter_count", 0),
        "scope": payload.get("scope", ""),
        "smoke_only": payload.get("smoke_only", False),
        "notes": "Step 5 checkpoint manifest; smoke checkpoints are not main evidence.",
    }
    manifest_path = output_dir / "checkpoint_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "checkpoint_path": project_relative(checkpoint_path, root),
        "checkpoint_hash": checkpoint_hash,
        "checkpoint_manifest_path": project_relative(manifest_path, root),
        "checkpoint_manifest_hash": sha256_file(manifest_path),
    }
