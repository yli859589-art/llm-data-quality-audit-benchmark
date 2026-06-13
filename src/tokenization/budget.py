from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .bpe_tokenizer import LightweightBPETokenizer
from .char_tokenizer import CharTokenizer
from .manifest import project_relative
from .validation import validate_budget_report


def _read_jsonl_texts(path: Path) -> list[str]:
    texts: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get("text")
        if isinstance(text, str):
            texts.append(text)
    return texts


def _load_tokenizer_from_manifest(manifest: dict[str, Any], root: Path):
    tokenizer_type = str(manifest["tokenizer_type"])
    model_path = root / str(manifest.get("model_path", "")) if manifest.get("model_path") else None
    vocab_path = root / str(manifest.get("vocab_path", "")) if manifest.get("vocab_path") else None
    if tokenizer_type == "lightweight_bpe_smoke":
        if model_path is None:
            raise ValueError("lightweight_bpe_smoke manifest missing model_path")
        return LightweightBPETokenizer.load(model_path)
    if tokenizer_type == "char":
        if vocab_path is None and model_path is None:
            raise ValueError("char manifest missing vocab/model path")
        return CharTokenizer.load(vocab_path or model_path)
    raise ValueError(f"budget checker does not load tokenizer_type={tokenizer_type}")


def count_jsonl_tokens(data_path: str | Path, tokenizer) -> int:
    return sum(tokenizer.count_tokens(text) for text in _read_jsonl_texts(Path(data_path)))


def compare_token_budgets_across_tokenizers(data_path: str | Path, tokenizers: dict[str, object]) -> dict[str, int]:
    return {name: count_jsonl_tokens(data_path, tokenizer) for name, tokenizer in tokenizers.items()}


def verify_budget_not_mislabeled(manifest: dict[str, Any], expected_tokenizer_type: str) -> None:
    actual = str(manifest.get("tokenizer_type", ""))
    if actual != expected_tokenizer_type:
        raise ValueError(f"expected tokenizer_type={expected_tokenizer_type}, got {actual}")
    if actual != "char" and str(manifest.get("training_scope")) == "step2_whitespace_proxy":
        raise ValueError("Step 2 whitespace proxy budget cannot be mislabeled as tokenizer-specific budget")


def build_token_budget_report(
    *,
    data_path: str | Path,
    tokenizer_manifest: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    tokenizer = _load_tokenizer_from_manifest(tokenizer_manifest, root)
    token_count = count_jsonl_tokens(data_path, tokenizer)
    report = {
        "status": "passed",
        "data_path": project_relative(data_path, root),
        "tokenizer_name": tokenizer_manifest["tokenizer_name"],
        "tokenizer_type": tokenizer_manifest["tokenizer_type"],
        "tokenizer_hash": tokenizer_manifest["tokenizer_hash"],
        "tokenizer_specific_token_count": token_count,
        "data_token_counter_type": "whitespace_proxy",
        "proxy_vs_tokenizer_warning": (
            "Step 2 whitespace counts are proxy counts. Step 3 tokenizer counts are tokenizer-specific "
            "and must not be mixed as equal training budgets."
        ),
    }
    validate_budget_report(report)
    return report


def write_token_budget_report(output_path: str | Path, report: dict[str, Any]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
