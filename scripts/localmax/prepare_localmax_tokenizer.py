from __future__ import annotations

import argparse

from localmax_utils import LOCALMAX_TOKENIZERS, gpt2_tokenizer, import_status, status_payload, write_json, write_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax/tokenizer.yaml")
    return parser.parse_args()


def main() -> None:
    _parse_args()
    blocking: list[str] = []
    tokenizer_ready = False
    tokenizer_meta = {
        "tokenizer_name": "gpt2",
        "tokenizer_type": "gpt2_bpe",
        "tokenizer_source": "transformers_gpt2",
        "vocab_size": None,
        "actual_gpt2_tokenizer_loaded": False,
        "char_level_mainline": False,
        "lightweight_bpe_smoke_mainline": False,
    }
    if not import_status("transformers")["available"]:
        blocking.append("transformers is unavailable; GPT-2 tokenizer cannot be loaded.")
    else:
        try:
            tokenizer = gpt2_tokenizer()
            tokenizer_meta.update(
                {
                    "vocab_size": int(getattr(tokenizer, "vocab_size", 0)),
                    "actual_gpt2_tokenizer_loaded": True,
                }
            )
            tokenizer_ready = True
        except Exception as exc:
            blocking.append(f"GPT-2 tokenizer load failed: {type(exc).__name__}: {exc}")
    manifest = status_payload(
        "tokenizer_manifest",
        tokenizer_ready,
        blocking,
        {
            **tokenizer_meta,
            "scope": "localmax_tokenizer",
            "localmax_mainline": True,
            "level3_mainline": False,
            "smoke_only": False,
            "lightweight_bpe_smoke": False,
            "token_counter_type": "gpt2_bpe",
            "tokenizer_budget_policy": {
                "recommended_token_budget_per_dataset": 50_000_000,
                "max_attempt_token_budget_per_dataset": 100_000_000,
                "minimum_localmax_dataset_tokens": 20_000_000,
            },
            "localmax_tokenizer_ready": tokenizer_ready,
            "completed": tokenizer_ready,
        },
    )
    write_json(LOCALMAX_TOKENIZERS / "gpt2" / "tokenizer_manifest.json", manifest)
    report = status_payload(
        "tokenizer",
        tokenizer_ready,
        blocking,
        {
            **tokenizer_meta,
            "localmax_tokenizer_ready": tokenizer_ready,
            "notes": [
                "GPT-2 tokenizer is the LocalMax mainline when this report is ready.",
                "Char-level and lightweight BPE smoke tokenizers are not treated as LocalMax mainline evidence.",
            ],
        },
    )
    write_report(report, "localmax_tokenizer_report", "LocalMax Tokenizer Report")
    print(f"LocalMax tokenizer: ready={tokenizer_ready}")


if __name__ == "__main__":
    main()
