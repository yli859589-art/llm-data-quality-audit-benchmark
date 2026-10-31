from __future__ import annotations

from pathlib import Path
from typing import Any


def _value(manifest: dict[str, Any], key: str, default: str = "") -> str:
    value = manifest.get(key, default)
    if value is None:
        return default
    return str(value)


def write_dataset_card(manifest: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "DATASET_CARD.md"
    lines = [
        f"# Dataset Card: {_value(manifest, 'dataset_key', _value(manifest, 'dataset'))}",
        "",
        "## Source",
        "",
        f"- Dataset: `{_value(manifest, 'dataset')}`",
        f"- Source: `{_value(manifest, 'source')}`",
        f"- Version: `{_value(manifest, 'version')}`",
        f"- License / terms: {_value(manifest, 'license_or_terms', 'verify upstream terms before release')}",
        f"- Download or streaming method: `{_value(manifest, 'download_or_streaming_method', _value(manifest, 'download_method'))}`",
        "",
        "## Status",
        "",
        f"- dataset_status: `{_value(manifest, 'dataset_status')}`",
        f"- dataset_scope: `{_value(manifest, 'dataset_scope')}`",
        f"- streaming sample: `{_value(manifest, 'is_streaming_sample')}`",
        f"- complete upstream corpus: `{_value(manifest, 'is_full_dataset')}`",
        f"- failure reason: {_value(manifest, 'failure_reason', 'none') or 'none'}",
        "",
        "## Sample Size",
        "",
        f"- sample_seed: `{_value(manifest, 'sample_seed')}`",
        f"- max_documents: `{_value(manifest, 'max_documents')}`",
        f"- max_tokens: `{_value(manifest, 'max_tokens')}`",
        f"- actual_documents: `{_value(manifest, 'actual_documents')}`",
        f"- actual_train_tokens: `{_value(manifest, 'actual_train_tokens')}`",
        f"- actual_validation_tokens: `{_value(manifest, 'actual_validation_tokens')}`",
        f"- actual_test_tokens: `{_value(manifest, 'actual_test_tokens')}`",
        "",
        "## Hashes",
        "",
        f"- content_hash: `{_value(manifest, 'content_hash', _value(manifest, 'corpus_sha256'))}`",
        f"- split_hash_train: `{_value(manifest, 'split_hash_train')}`",
        f"- split_hash_dev: `{_value(manifest, 'split_hash_dev')}`",
        f"- split_hash_test: `{_value(manifest, 'split_hash_test')}`",
        "",
        "## Known Limitations",
        "",
        "- This card describes the prepared sample or failure state recorded by the repository.",
        "- Streaming samples are bounded samples and must not be described as complete upstream corpora.",
        "- Failed or insufficient samples remain part of the audit trail instead of being replaced by fallback fixtures.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
