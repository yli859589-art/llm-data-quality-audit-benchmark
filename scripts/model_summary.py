from __future__ import annotations

import argparse

from experiment_utils import load_json_yaml, root, write_json


def estimate_parameters(config: dict[str, object]) -> int:
    hidden = int(config["hidden_size"])
    layers = int(config["layers"])
    context = int(config["context_length"])
    vocab = 256 if "character" in str(config.get("vocab_type", "")) else 50_000
    embeddings = vocab * hidden + context * hidden
    per_layer = 4 * hidden * hidden + 8 * hidden * hidden + 4 * hidden
    final = hidden * vocab
    return embeddings + layers * per_layer + final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    card = dict(config)
    card["estimated_parameters"] = estimate_parameters(config)
    card["parameter_count_note"] = (
        "Approximate architecture-card estimate, not a trained checkpoint."
    )
    output = root / "artifacts" / "model_cards" / f"{config['model_key']}.json"
    write_json(output, card)
    print(f"Model card: {output}")
    print(f"Estimated parameters: {card['estimated_parameters']}")


if __name__ == "__main__":
    main()
