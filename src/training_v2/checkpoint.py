from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import torch
from torch import nn

from tokenization.manifest import sha256_file


FULL_STATE_FORMAT = "p0-02.full-training-state.v1"


def capture_rng_state(*, include_cuda: bool = False) -> dict[str, Any]:
    state: dict[str, Any] = {"python": random.getstate(), "torch_cpu": torch.get_rng_state()}
    if include_cuda and torch.cuda.is_available():
        state["torch_cuda"] = torch.cuda.get_rng_state_all()
    return state


def restore_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    torch.set_rng_state(state["torch_cpu"])
    if "torch_cuda" in state and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def save_full_training_state(
    *, model: nn.Module, optimizer: torch.optim.Optimizer, path: Path,
    step: int, tokens_seen: int, sampler_state: dict[str, Any],
    model_config: dict[str, Any], training_config: dict[str, Any],
    data_manifest_hash: str, data_version: str, scheduler: Any | None = None,
) -> dict[str, Any]:
    """Persist an exact-resume checkpoint; never label a weights-only file resume."""
    payload = {
        "checkpoint_format_version": FULL_STATE_FORMAT,
        "resume_capability": "exact_resume",
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict() if scheduler is not None else None,
        "rng_state": capture_rng_state(include_cuda=any(parameter.is_cuda for parameter in model.parameters())), "sampler_state": sampler_state,
        "step": step, "tokens_seen": tokens_seen,
        "model_config": model_config, "training_config": training_config,
        "data_manifest_hash": data_manifest_hash, "data_version": data_version,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return {"checkpoint_path": str(path), "checkpoint_sha256": sha256_file(path), "checkpoint_format_version": FULL_STATE_FORMAT, "resume_capability": "exact_resume"}


def load_training_state(*, model: nn.Module, optimizer: torch.optim.Optimizer, path: Path, scheduler: Any | None = None) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if payload.get("checkpoint_format_version") != FULL_STATE_FORMAT:
        state = payload.get("model_state_dict") or payload.get("model_state_dict_fp16")
        if not isinstance(state, dict):
            raise ValueError("checkpoint has no recognized model state")
        model.load_state_dict({key: value.float() if hasattr(value, "float") else value for key, value in state.items()})
        return {"resume_capability": "weights_only_initialization", "step": 0, "tokens_seen": 0, "sampler_state": {}}
    model.load_state_dict(payload["model_state_dict"])
    optimizer.load_state_dict(payload["optimizer_state_dict"])
    if scheduler is not None and payload.get("scheduler_state_dict") is not None:
        scheduler.load_state_dict(payload["scheduler_state_dict"])
    restore_rng_state(payload["rng_state"])
    return {"resume_capability": "exact_resume", "step": int(payload["step"]), "tokens_seen": int(payload["tokens_seen"]), "sampler_state": dict(payload["sampler_state"]), "data_manifest_hash": payload.get("data_manifest_hash", ""), "data_version": payload.get("data_version", "")}


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
