from __future__ import annotations

from pathlib import Path
from typing import Any

from .streaming_loader import take_text_rows


def load_huggingface_texts(config: dict[str, Any], root: Path) -> list[str]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Hugging Face `datasets` is not installed. Install it or use a smoke "
            "config with an explicit fallback fixture."
        ) from exc

    dataset_name = config["hf_dataset"]
    subset = config.get("hf_subset")
    split = config.get("hf_split", "train")
    streaming = bool(config.get("streaming", False))
    cache_dir = config.get("cache_dir")
    cache_path = root / cache_dir if cache_dir else None
    kwargs: dict[str, Any] = {"split": split, "streaming": streaming}
    if cache_path is not None:
        kwargs["cache_dir"] = str(cache_path)
    if subset:
        rows = load_dataset(dataset_name, subset, **kwargs)
    else:
        rows = load_dataset(dataset_name, **kwargs)
    return take_text_rows(
        rows,
        text_field=str(config.get("text_field", "text")),
        max_documents=config.get("max_documents"),
    )
