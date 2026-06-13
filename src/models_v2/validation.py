from __future__ import annotations

from .config import ModelConfig, VALID_SCALE_CLASSES
from .parameter_count import estimate_decoder_lm_parameters


def validate_model_config(config: ModelConfig) -> None:
    if config.model_family != "decoder_lm":
        raise ValueError("Step 5 only supports model_family=decoder_lm")
    if config.scale_class not in VALID_SCALE_CLASSES:
        raise ValueError(f"invalid scale_class: {config.scale_class}")
    if config.vocab_size <= 1:
        raise ValueError("vocab_size must be > 1")
    if config.context_length < 2:
        raise ValueError("context_length must be >= 2")
    if config.num_layers < 1:
        raise ValueError("num_layers must be >= 1")
    if config.hidden_size < 1:
        raise ValueError("hidden_size must be positive")
    if config.num_heads < 1:
        raise ValueError("num_heads must be positive")
    if config.hidden_size % config.num_heads != 0:
        raise ValueError("hidden_size must be divisible by num_heads")
    if not 0 <= config.dropout < 1:
        raise ValueError("dropout must be in [0, 1)")
    expected = estimate_decoder_lm_parameters(
        vocab_size=config.vocab_size,
        context_length=config.context_length,
        num_layers=config.num_layers,
        hidden_size=config.hidden_size,
        num_heads=config.num_heads,
        tie_embeddings=config.tie_embeddings,
    )
    if config.parameter_count != expected:
        raise ValueError(
            f"parameter_count mismatch: expected {expected}, got {config.parameter_count}"
        )
