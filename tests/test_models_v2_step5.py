from __future__ import annotations

import pytest

from models_v2.config import ModelConfig, load_model_config
from models_v2.decoder_lm import DecoderLM, count_parameters
from models_v2.parameter_count import estimate_decoder_lm_parameters


def test_tiny_bpe_model_config_parameter_count_matches_model() -> None:
    config = load_model_config("configs/models_v2/tiny_smoke_bpe.yaml")
    model = DecoderLM(config)

    assert config.scale_class == "tiny_smoke"
    assert count_parameters(model) == config.parameter_count
    assert config.parameter_count == estimate_decoder_lm_parameters(
        vocab_size=config.vocab_size,
        context_length=config.context_length,
        num_layers=config.num_layers,
        hidden_size=config.hidden_size,
        num_heads=config.num_heads,
        tie_embeddings=config.tie_embeddings,
    )


def test_model_config_rejects_hidden_size_not_divisible_by_heads() -> None:
    payload = load_model_config("configs/models_v2/tiny_smoke_bpe.yaml").to_dict()
    payload["hidden_size"] = 10
    payload["num_heads"] = 3
    payload["parameter_count"] = 1

    with pytest.raises(ValueError, match="hidden_size must be divisible"):
        ModelConfig.from_mapping(payload)


def test_protocol_model_configs_are_marked_not_completed_scales() -> None:
    medium = load_model_config("configs/models_v2/medium_100m_bpe_protocol.yaml")
    large_lite = load_model_config("configs/models_v2/large_lite_300m_bpe_protocol.yaml")

    assert medium.scale_class == "medium_protocol"
    assert large_lite.scale_class == "large_lite_protocol"
