from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import BaseTokenizer

MANIFEST_VERSION = "step3.tokenizer_manifest.v1"
VALID_TOKENIZER_TYPES = {
    "char",
    "sentencepiece_bpe",
    "hf_bpe",
    "lightweight_bpe_smoke",
    "gpt2_optional",
}
VALID_SCOPES = {"smoke", "sample", "main_protocol", "legacy_current", "implemented_but_not_run"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def project_relative(path: str | Path, root: Path) -> str:
    if not path:
        return ""
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def _path_hash(path: str | Path) -> str:
    if not path:
        return ""
    value = Path(path)
    return sha256_file(value) if value.exists() else ""


def combined_tokenizer_hash(
    *,
    tokenizer_type: str,
    tokenizer_name: str,
    model_path: str | Path = "",
    vocab_path: str | Path = "",
    extra: dict[str, Any] | None = None,
) -> str:
    payload = {
        "tokenizer_type": tokenizer_type,
        "tokenizer_name": tokenizer_name,
        "model_hash": _path_hash(model_path),
        "vocab_hash": _path_hash(vocab_path),
        "extra": extra or {},
    }
    return sha256_json(payload)


def create_tokenizer_manifest(
    *,
    tokenizer: BaseTokenizer | None,
    root: Path,
    tokenizer_name: str,
    tokenizer_type: str,
    scope: str,
    level3_mainline: bool,
    vocab_size_requested: int,
    vocab_size_actual: int,
    training_data_path: str,
    training_scope: str,
    seed: int,
    normalization: str,
    model_path: str,
    vocab_path: str,
    optional_dependency: str = "",
    optional_dependency_available: bool = False,
    fallback_used: bool = False,
    fallback_type: str = "",
    smoke_only: bool = False,
    implemented_but_not_run: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    training_path = root / training_data_path if training_data_path and not Path(training_data_path).is_absolute() else Path(training_data_path) if training_data_path else None
    training_hash = sha256_file(training_path) if training_path is not None and training_path.exists() else ""
    model_abs = root / model_path if model_path and not Path(model_path).is_absolute() else Path(model_path) if model_path else Path()
    vocab_abs = root / vocab_path if vocab_path and not Path(vocab_path).is_absolute() else Path(vocab_path) if vocab_path else Path()
    tokenizer_hash = combined_tokenizer_hash(
        tokenizer_type=tokenizer_type,
        tokenizer_name=tokenizer_name,
        model_path=model_abs if model_path else "",
        vocab_path=vocab_abs if vocab_path else "",
        extra={
            "vocab_size_actual": vocab_size_actual,
            "seed": seed,
            "normalization": normalization,
            "implemented_but_not_run": implemented_but_not_run,
        },
    )
    if tokenizer is not None and not implemented_but_not_run:
        tokenizer_hash = tokenizer.tokenizer_hash

    return {
        "manifest_version": MANIFEST_VERSION,
        "tokenizer_name": tokenizer_name,
        "tokenizer_type": tokenizer_type,
        "scope": scope,
        "level3_mainline": bool(level3_mainline),
        "vocab_size_requested": vocab_size_requested,
        "vocab_size_actual": vocab_size_actual,
        "training_data_path": training_data_path,
        "training_data_hash": training_hash,
        "training_scope": training_scope,
        "seed": seed,
        "normalization": normalization,
        "model_path": project_relative(model_abs, root) if model_path else "",
        "vocab_path": project_relative(vocab_abs, root) if vocab_path else "",
        "tokenizer_hash": tokenizer_hash,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "optional_dependency": optional_dependency,
        "optional_dependency_available": bool(optional_dependency_available),
        "fallback_used": bool(fallback_used),
        "fallback_type": fallback_type,
        "smoke_only": bool(smoke_only),
        "implemented_but_not_run": bool(implemented_but_not_run),
        "notes": notes,
    }


def write_tokenizer_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
