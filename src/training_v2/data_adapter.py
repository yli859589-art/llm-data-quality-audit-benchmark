from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from tokenization.bpe_tokenizer import LightweightBPETokenizer
from tokenization.char_tokenizer import CharTokenizer
from tokenization.manifest import sha256_file


@dataclass(frozen=True)
class TokenizedTrainingData:
    token_ids: list[int]
    blocks_x: torch.Tensor
    blocks_y: torch.Tensor
    summary: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_texts(path: Path) -> list[str]:
    texts: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get("text")
        if isinstance(text, str) and text:
            texts.append(text)
    return texts


def _resolve(path: str, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def load_tokenizer_from_manifest(manifest_path: str | Path, root: Path):
    manifest_file = _resolve(str(manifest_path), root)
    manifest = _read_json(manifest_file)
    tokenizer_type = str(manifest.get("tokenizer_type", ""))
    if tokenizer_type == "lightweight_bpe_smoke":
        model_path = _resolve(str(manifest.get("model_path", "")), root)
        if not model_path.exists():
            raise ValueError(f"BPE tokenizer model not found: {model_path}")
        return LightweightBPETokenizer.load(model_path), manifest
    if tokenizer_type == "char":
        path_value = str(manifest.get("vocab_path") or manifest.get("model_path") or "")
        if not path_value:
            raise ValueError("char tokenizer manifest missing vocab_path/model_path")
        return CharTokenizer.load(_resolve(path_value, root)), manifest
    if manifest.get("implemented_but_not_run") is True:
        raise ValueError(f"Tokenizer is implemented_but_not_run and cannot encode: {tokenizer_type}")
    raise ValueError(f"Unsupported Step 5 tokenizer type: {tokenizer_type}")


def _make_blocks(token_ids: list[int], context_length: int) -> tuple[torch.Tensor, torch.Tensor]:
    if len(token_ids) <= context_length + 1:
        raise ValueError("encoded token stream is too short for context_length")
    xs = []
    ys = []
    for start in range(0, len(token_ids) - context_length):
        chunk = token_ids[start : start + context_length + 1]
        xs.append(chunk[:-1])
        ys.append(chunk[1:])
    return torch.tensor(xs, dtype=torch.long), torch.tensor(ys, dtype=torch.long)


def build_tokenized_training_data(
    *,
    dataset_path: str | Path,
    dataset_manifest_path: str | Path,
    tokenizer_manifest_path: str | Path,
    context_length: int,
    root: Path,
) -> TokenizedTrainingData:
    data_file = _resolve(str(dataset_path), root)
    dataset_manifest_file = _resolve(str(dataset_manifest_path), root)
    tokenizer, tokenizer_manifest = load_tokenizer_from_manifest(tokenizer_manifest_path, root)
    texts = _read_jsonl_texts(data_file)
    token_ids: list[int] = []
    for text in texts:
        token_ids.extend(tokenizer.encode(text))
    blocks_x, blocks_y = _make_blocks(token_ids, context_length)
    dataset_manifest = _read_json(dataset_manifest_file) if dataset_manifest_file.exists() else {}
    summary = {
        "num_documents": len(texts),
        "encoded_tokens": len(token_ids),
        "num_blocks": int(blocks_x.shape[0]),
        "context_length": context_length,
        "tokenizer_type": tokenizer_manifest.get("tokenizer_type", ""),
        "tokenizer_hash": tokenizer_manifest.get("tokenizer_hash", ""),
        "data_hash": sha256_file(data_file),
        "dataset_manifest_hash": sha256_file(dataset_manifest_file) if dataset_manifest_file.exists() else "",
        "dataset_token_counter_type": dataset_manifest.get("token_counter_type", ""),
        "token_budget_note": "Tokenizer-specific counts are used here; Step 2 whitespace proxy counts are not treated as BPE training tokens.",
    }
    return TokenizedTrainingData(token_ids=token_ids, blocks_x=blocks_x, blocks_y=blocks_y, summary=summary)
