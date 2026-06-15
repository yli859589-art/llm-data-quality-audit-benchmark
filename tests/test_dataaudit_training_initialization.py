from __future__ import annotations

from dataaudit_lm.models.config import DecoderLMConfig
from dataaudit_lm.training.initialization import create_initialized_model


def test_same_seed_same_initialization_fingerprint_across_methods() -> None:
    config = DecoderLMConfig(vocab_size=32, context_length=8, embedding_dim=8, hidden_dim=8)

    _model_a, fp_a = create_initialized_model(42, config)
    _model_b, fp_b = create_initialized_model(42, config)
    _model_c, fp_c = create_initialized_model(13, config)

    assert fp_a == fp_b
    assert fp_a != fp_c
