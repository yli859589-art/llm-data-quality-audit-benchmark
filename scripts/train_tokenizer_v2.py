from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root
from tokenization.base import TokenizerConfig
from tokenization.bpe_tokenizer import LightweightBPETokenizer
from tokenization.char_tokenizer import CharTokenizer
from tokenization.gpt2_tokenizer import GPT2OptionalTokenizer
from tokenization.manifest import create_tokenizer_manifest, write_tokenizer_manifest
from tokenization.validation import validate_tokenizer_manifest


def _read_jsonl_texts(path: Path) -> list[str]:
    texts: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text)
    return texts


def _write_vocab(path: Path, vocab: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(vocab, indent=2, sort_keys=True), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train or register Step 3 tokenizer artifacts.")
    parser.add_argument("--tokenizer-type", required=True, choices=["char", "bpe", "gpt2"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--scope", required=True, choices=["smoke", "sample", "main_protocol", "legacy_current", "implemented_but_not_run"])
    parser.add_argument("--vocab-size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest-output", required=True)
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--normalization", default="identity")
    return parser.parse_args()


def _config(args: argparse.Namespace, model_path: Path, vocab_path: Path) -> TokenizerConfig:
    tokenizer_type = {
        "char": "char",
        "bpe": "lightweight_bpe_smoke",
        "gpt2": "gpt2_optional",
    }[args.tokenizer_type]
    return TokenizerConfig(
        tokenizer_name=args.name,
        tokenizer_type=tokenizer_type,
        vocab_size=args.vocab_size,
        training_data_path=args.data,
        training_scope=args.scope,
        seed=args.seed,
        normalization=args.normalization,
        model_path=model_path.as_posix(),
        vocab_path=vocab_path.as_posix(),
        manifest_path=args.manifest_output,
        optional_dependency="tiktoken_or_transformers" if args.tokenizer_type == "gpt2" else "",
        fallback_allowed=args.allow_fallback,
        smoke_only=args.scope == "smoke",
        scope=args.scope,
        level3_mainline=False,
    )


def _write_manifest(
    args: argparse.Namespace,
    *,
    tokenizer,
    model_path: Path | None,
    vocab_path: Path | None,
    **extra,
) -> dict[str, object]:
    manifest = create_tokenizer_manifest(
        tokenizer=tokenizer,
        root=root,
        tokenizer_name=args.name,
        tokenizer_type=extra["tokenizer_type"],
        scope=args.scope,
        level3_mainline=False,
        vocab_size_requested=args.vocab_size,
        vocab_size_actual=extra["vocab_size_actual"],
        training_data_path=args.data,
        training_scope=args.scope,
        seed=args.seed,
        normalization=args.normalization,
        model_path=model_path.as_posix() if model_path is not None else "",
        vocab_path=vocab_path.as_posix() if vocab_path is not None else "",
        optional_dependency=extra.get("optional_dependency", ""),
        optional_dependency_available=extra.get("optional_dependency_available", False),
        fallback_used=extra.get("fallback_used", False),
        fallback_type=extra.get("fallback_type", ""),
        smoke_only=args.scope == "smoke",
        implemented_but_not_run=extra.get("implemented_but_not_run", False),
        notes=extra.get("notes", ""),
    )
    validate_tokenizer_manifest(manifest, root)
    write_tokenizer_manifest(root / args.manifest_output, manifest)
    return manifest


def main() -> None:
    args = _parse_args()
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    texts = _read_jsonl_texts(root / args.data) if (root / args.data).exists() else []

    if args.tokenizer_type == "char":
        model_path = output_dir / "char_tokenizer.json"
        vocab_path = output_dir / "char_vocab.json"
        tokenizer = CharTokenizer(_config(args, model_path, vocab_path)).train(texts)
        tokenizer.save(vocab_path)
        model_path.write_text(vocab_path.read_text(encoding="utf-8"), encoding="utf-8")
        manifest = _write_manifest(
            args,
            tokenizer=tokenizer,
            model_path=model_path,
            vocab_path=vocab_path,
            tokenizer_type="char",
            vocab_size_actual=tokenizer.vocab_size,
            notes="Char tokenizer is legacy/current evidence, not Level 3 modern tokenizer mainline.",
        )
    elif args.tokenizer_type == "bpe":
        if not args.allow_fallback:
            raise SystemExit("Step 3 smoke BPE requires --allow-fallback when SentencePiece/HF tokenizers are not configured.")
        model_path = output_dir / "tokenizer.json"
        vocab_path = output_dir / "vocab.json"
        tokenizer = LightweightBPETokenizer(_config(args, model_path, vocab_path)).train(texts)
        tokenizer.save(model_path)
        _write_vocab(vocab_path, tokenizer.vocab)
        manifest = _write_manifest(
            args,
            tokenizer=tokenizer,
            model_path=model_path,
            vocab_path=vocab_path,
            tokenizer_type="lightweight_bpe_smoke",
            vocab_size_actual=tokenizer.vocab_size,
            fallback_used=True,
            fallback_type="lightweight_bpe_smoke",
            notes="Smoke-only lightweight BPE fallback. Not BPE16k/BPE32k mainline evidence.",
        )
    else:
        tokenizer = GPT2OptionalTokenizer()
        if not tokenizer.available:
            manifest = _write_manifest(
                args,
                tokenizer=tokenizer,
                model_path=None,
                vocab_path=None,
                tokenizer_type="gpt2_optional",
                vocab_size_actual=0,
                optional_dependency="tiktoken_or_transformers",
                optional_dependency_available=False,
                implemented_but_not_run=True,
                notes=f"GPT-2 optional tokenizer unavailable: {tokenizer.unavailable_reason}",
            )
        else:
            raise SystemExit("GPT-2 optional tokenizer is available but Step 3 does not save external GPT-2 assets.")

    print(json.dumps({"manifest_path": args.manifest_output, "manifest": manifest}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
