from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch

from dataaudit_lm.integrity.hashing import sha256_file, sha256_json
from dataaudit_lm.models.config import DecoderLMConfig
from dataaudit_lm.models.decoder_lm import TinyDecoderLM


@dataclass(frozen=True)
class InitializationManifest:
    seed: int
    model_config: dict[str, int | float]
    warm_start: bool
    initialization_fingerprint: str
    state_path: str | None = None
    state_sha256: str | None = None


def set_training_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def create_initialized_model(seed: int, config: DecoderLMConfig) -> tuple[TinyDecoderLM, str]:
    set_training_seed(seed)
    model = TinyDecoderLM(config)
    state_summary = {
        name: tensor.detach().cpu().numpy().round(8).tolist()
        for name, tensor in model.state_dict().items()
    }
    fingerprint = sha256_json({"seed": seed, "config": config.to_dict(), "state": state_summary})
    return model, fingerprint


def save_initialization_artifact(
    *,
    seed: int,
    config: DecoderLMConfig,
    output_dir: Path,
) -> InitializationManifest:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, fingerprint = create_initialized_model(seed, config)
    state_path = output_dir / f"initial_state_seed_{seed}.pt"
    torch.save({"config": config.to_dict(), "state_dict": model.state_dict()}, state_path)
    try:
        display_state_path = state_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        display_state_path = state_path.name
    return InitializationManifest(
        seed=seed,
        model_config=config.to_dict(),
        warm_start=False,
        initialization_fingerprint=fingerprint,
        state_path=display_state_path,
        state_sha256=sha256_file(state_path),
    )


def manifest_to_dict(manifest: InitializationManifest) -> dict[str, object]:
    return asdict(manifest)
