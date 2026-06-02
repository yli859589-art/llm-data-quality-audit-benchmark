from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import load_yaml_config
from .dataset import CorpusSource, load_public_corpus, sha256_text


@dataclass(frozen=True)
class ConfiguredDataset:
    text: str
    source: CorpusSource
    used_fallback: bool
    configuration: dict[str, Any]


def _local_text(root: Path, config: dict[str, Any]) -> ConfiguredDataset:
    path = root / config["local_path"]
    if config["dataset_name"] == "tiny_shakespeare":
        text, source = load_public_corpus(path)
    else:
        text = path.read_text(encoding="utf-8")
        source = CorpusSource(
            dataset_name=config["dataset_name"],
            path=path.relative_to(root).as_posix(),
            source=config["source"],
            url=config.get("url", ""),
            sha256=sha256_text(text),
            chars=len(text),
            license_or_usage_note=config["license_or_usage_note"],
            split=config.get("split", "train"),
        )
    return ConfiguredDataset(text, source, False, config)


def load_configured_dataset(
    config_path: str | Path,
    *,
    root: str | Path,
    allow_network: bool = False,
) -> ConfiguredDataset:
    """Load local text by default and make Hugging Face downloads explicit."""
    root_path = Path(root)
    config = load_yaml_config(config_path)
    provider = config["provider"]
    if provider == "local":
        return _local_text(root_path, config)
    if provider != "huggingface":
        raise ValueError(f"Unsupported dataset provider: {provider}")
    if not allow_network:
        fallback = load_yaml_config(root_path / config["offline_fallback_config"])
        loaded = _local_text(root_path, fallback)
        return ConfiguredDataset(loaded.text, loaded.source, True, config)
    try:
        from datasets import load_dataset  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError(
            "Optional Hugging Face support requires: python -m pip install datasets"
        ) from error
    dataset = load_dataset(
        config["hf_path"],
        config.get("hf_name"),
        split=config.get("split", "train"),
        streaming=True,
    )
    field = config.get("text_field", "text")
    max_documents = int(config.get("sample_documents", 1000))
    texts = []
    for index, row in enumerate(dataset):
        if index >= max_documents:
            break
        value = row.get(field)
        if value:
            texts.append(str(value))
    text = "\n\n".join(texts)
    source = CorpusSource(
        dataset_name=config["dataset_name"],
        path="streamed_optional_dataset",
        source=config["source"],
        url=config.get("url", ""),
        sha256=sha256_text(text),
        chars=len(text),
        license_or_usage_note=config["license_or_usage_note"],
        split=config.get("split", "train"),
    )
    return ConfiguredDataset(text, source, False, config)
