from __future__ import annotations

from dataclasses import asdict

from analysis.quality_error_analysis import js_divergence, length_distribution, token_distribution
from filters.hdqspp_v2 import HDQSv2Config, config_from_mapping


def calibration_objective(
    raw_train_documents: list[str],
    selected_documents: list[str],
    dev_documents: list[str],
) -> dict[str, float]:
    raw_tokens = token_distribution(raw_train_documents, top_k=5000)
    selected_tokens = token_distribution(selected_documents, top_k=5000)
    dev_tokens = token_distribution(dev_documents, top_k=5000)
    raw_lengths = length_distribution(raw_train_documents)
    selected_lengths = length_distribution(selected_documents)
    dev_lengths = length_distribution(dev_documents)
    return {
        "token_js_selected_vs_raw": js_divergence(selected_tokens, raw_tokens),
        "token_js_selected_vs_dev": js_divergence(selected_tokens, dev_tokens),
        "length_js_selected_vs_raw": js_divergence(selected_lengths, raw_lengths),
        "length_js_selected_vs_dev": js_divergence(selected_lengths, dev_lengths),
        "retention_rate": len(selected_documents) / max(1, len(raw_train_documents)),
    }


def frozen_config_payload(config: HDQSv2Config) -> dict[str, object]:
    return {
        "method": "hdqspp_v2",
        "config": asdict(config),
        "selection_boundary": "train/dev only; test split not used for tuning",
    }


def load_hdqspp_v2_config(payload: dict[str, object] | None) -> HDQSv2Config:
    return config_from_mapping(payload)
