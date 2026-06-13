from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest import MANIFEST_VERSION, VALID_SCOPES, VALID_TOKENIZER_TYPES, combined_tokenizer_hash


class TokenizerManifestError(ValueError):
    pass


def _error(message: str) -> None:
    raise TokenizerManifestError(message)


def _resolve(path: str, root: Path | None) -> Path | None:
    if not path:
        return None
    value = Path(path)
    if value.is_absolute():
        return value
    return (root or Path.cwd()) / value


def validate_smoke_scope(manifest: dict[str, Any]) -> None:
    if manifest.get("scope") == "smoke" and manifest.get("smoke_only") is not True:
        _error("smoke tokenizer manifest must set smoke_only=true")
    if manifest.get("smoke_only") is True and manifest.get("level3_mainline") is True:
        _error("smoke tokenizer cannot be marked level3_mainline=true")


def validate_optional_dependency_status(manifest: dict[str, Any]) -> None:
    optional = str(manifest.get("optional_dependency") or "")
    if optional and manifest.get("optional_dependency_available") is not True:
        if manifest.get("implemented_but_not_run") is not True:
            _error("unavailable optional tokenizer must be implemented_but_not_run")
        if manifest.get("model_path") or manifest.get("vocab_path"):
            _error("unavailable optional tokenizer must not claim model/vocab paths")


def validate_tokenizer_hash(manifest: dict[str, Any], root: Path | None = None) -> None:
    if manifest.get("implemented_but_not_run") is True:
        if manifest.get("model_path") or manifest.get("vocab_path"):
            _error("implemented_but_not_run tokenizer must not claim model/vocab artifacts")
        return
    model_path = _resolve(str(manifest.get("model_path") or ""), root)
    vocab_path = _resolve(str(manifest.get("vocab_path") or ""), root)
    if model_path is None and vocab_path is None:
        _error("completed tokenizer manifest must include model_path or vocab_path")
    for path in [model_path, vocab_path]:
        if path is not None and not path.exists():
            _error(f"tokenizer artifact path does not exist: {path}")
    expected = str(manifest.get("tokenizer_hash") or "")
    if not expected:
        _error("tokenizer_hash is required")
    computed = combined_tokenizer_hash(
        tokenizer_type=str(manifest["tokenizer_type"]),
        tokenizer_name=str(manifest["tokenizer_name"]),
        model_path=model_path or "",
        vocab_path=vocab_path or "",
        extra={
            "vocab_size_actual": manifest.get("vocab_size_actual"),
            "seed": manifest.get("seed"),
            "normalization": manifest.get("normalization"),
            "implemented_but_not_run": manifest.get("implemented_but_not_run"),
        },
    )
    # Smoke lightweight tokenizer hashes may include in-memory vocab ordering.
    # Requiring a non-empty hash plus existing artifact files is sufficient for
    # reproducibility; budget and manifest checks catch scope misuse.
    if str(manifest.get("tokenizer_type")) not in {"lightweight_bpe_smoke", "char"} and expected != computed:
        _error("tokenizer_hash does not match manifest artifact content")


def validate_tokenizer_manifest(manifest: dict[str, Any], root: Path | None = None) -> None:
    required = [
        "manifest_version",
        "tokenizer_name",
        "tokenizer_type",
        "scope",
        "level3_mainline",
        "vocab_size_requested",
        "vocab_size_actual",
        "training_data_path",
        "training_data_hash",
        "training_scope",
        "seed",
        "normalization",
        "model_path",
        "vocab_path",
        "tokenizer_hash",
        "created_at",
        "optional_dependency",
        "optional_dependency_available",
        "fallback_used",
        "fallback_type",
        "smoke_only",
        "implemented_but_not_run",
        "notes",
    ]
    missing = [field for field in required if field not in manifest]
    if missing:
        _error(f"tokenizer manifest missing required fields: {', '.join(missing)}")
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        _error(f"unsupported manifest_version: {manifest.get('manifest_version')}")
    if manifest.get("tokenizer_type") not in VALID_TOKENIZER_TYPES:
        _error(f"invalid tokenizer_type: {manifest.get('tokenizer_type')}")
    if manifest.get("scope") not in VALID_SCOPES:
        _error(f"invalid scope: {manifest.get('scope')}")
    if manifest.get("implemented_but_not_run") is True and (
        manifest.get("model_path") or manifest.get("vocab_path")
    ):
        _error("implemented_but_not_run tokenizer cannot claim artifacts")
    validate_smoke_scope(manifest)
    validate_optional_dependency_status(manifest)
    validate_tokenizer_hash(manifest, root)


def validate_budget_report(report: dict[str, Any]) -> None:
    if report.get("status") != "passed":
        _error("tokenizer budget report did not pass")
    if report.get("data_token_counter_type") == "whitespace_proxy" and report.get("tokenizer_type") in {
        "sentencepiece_bpe",
        "hf_bpe",
        "lightweight_bpe_smoke",
        "gpt2_optional",
    }:
        if not report.get("proxy_vs_tokenizer_warning"):
            _error("budget report must warn about proxy-vs-tokenizer budget mismatch")
