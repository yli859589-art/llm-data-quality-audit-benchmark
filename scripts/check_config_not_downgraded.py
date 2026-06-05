from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from experiment_utils import load_json_yaml


def main() -> None:
    dev = load_json_yaml("configs/experiments/dev.yaml")
    data = load_json_yaml(dev["dataset_config"])
    model = load_json_yaml("configs/models/small.yaml")
    errors = []
    if dev["dataset_config"] != "configs/data/wikitext2_paper.yaml":
        errors.append("dev config must target configs/data/wikitext2_paper.yaml")
    if dev.get("allow_fallback_in_data") is not False:
        errors.append("dev config must not allow fallback")
    if dev.get("required_real_data") is not True:
        errors.append("dev config must require real data")
    if dev.get("model_config") != "configs/models/small.yaml":
        errors.append("dev config must target configs/models/small.yaml")
    expected = {
        "raw",
        "random_same_keep_rate",
        "length_filter",
        "dedup_only",
        "hdqspp",
        "hdqspp_v2",
        "hdqspp_v2_no_token_frequency",
        "hdqspp_v3",
    }
    if set(dev.get("baselines", [])) != expected:
        errors.append(f"dev baselines must be exactly {sorted(expected)}")
    if "configs/filters/hdqspp_v2.yaml" not in str(dev.get("filter_configs", {})):
        errors.append("dev config must register configs/filters/hdqspp_v2.yaml")
    if "configs/filters/hdqspp_v3.yaml" not in str(dev.get("filter_configs", {})):
        errors.append("dev config must register configs/filters/hdqspp_v3.yaml")
    if data.get("allow_fallback") is not False or data.get("required_real_data") is not True:
        errors.append("wikitext2_paper must forbid fallback and require real data")
    if model.get("model_key") != "small":
        errors.append("small model config must retain model_key=small")
    if model.get("vocab_type") != "character_shared":
        errors.append("small model config must match actual shared character tokenizer")
    if errors:
        raise SystemExit("Config downgrade check failed." + "\n" + "\n".join(errors))
    print("Config downgrade check: ok")


if __name__ == "__main__":
    main()
