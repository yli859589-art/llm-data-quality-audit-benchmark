from __future__ import annotations


def estimate_decoder_lm_parameters(
    *,
    vocab_size: int,
    context_length: int,
    num_layers: int,
    hidden_size: int,
    num_heads: int,
    tie_embeddings: bool,
) -> int:
    """Estimate parameters for the Step 5 decoder-only LM architecture."""
    if hidden_size % num_heads != 0:
        raise ValueError("hidden_size must be divisible by num_heads")
    token_embedding = vocab_size * hidden_size
    position_embedding = context_length * hidden_size
    attention = 4 * hidden_size * hidden_size + 4 * hidden_size
    feed_forward = (hidden_size * 4 * hidden_size) + (4 * hidden_size * hidden_size)
    feed_forward_bias = 4 * hidden_size + hidden_size
    layer_norms = 4 * hidden_size
    per_layer = attention + feed_forward + feed_forward_bias + layer_norms
    final_norm = 2 * hidden_size
    lm_head = 0 if tie_embeddings else hidden_size * vocab_size + vocab_size
    return int(token_embedding + position_embedding + num_layers * per_layer + final_norm + lm_head)
