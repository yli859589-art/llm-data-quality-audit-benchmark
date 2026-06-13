from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()
CONFIG_ROOT = ROOT / "configs" / "level3"


def _load(name: str) -> dict:
    return json.loads((CONFIG_ROOT / name).read_text(encoding="utf-8"))


def test_level3_protocol_configs_are_protocol_only() -> None:
    required = [
        "data_matrix.yaml",
        "data_sources.yaml",
        "token_budget.yaml",
        "tokenizers.yaml",
        "filter_matrix.yaml",
        "model_matrix.yaml",
        "training_matrix.yaml",
        "evaluation_matrix.yaml",
        "mechanism_matrix.yaml",
        "statistics_protocol.yaml",
        "compute_budget.yaml",
        "artifact_paths.yaml",
        "claim_boundary.yaml",
    ]
    for name in required:
        payload = _load(name)
        assert payload["step"] == "step10A_level3_heavy_protocol_freeze"
        assert payload["protocol_only"] is True
        assert payload["completed"] is False


def test_level3_data_and_token_budget_floor() -> None:
    data = _load("data_matrix.yaml")
    required_datasets = [item for item in data["datasets"] if item["required"] is True]

    assert data["token_count_type"] == "tokenizer_specific_bpe_tokens"
    assert len(required_datasets) >= 3
    assert {item["dataset_id"] for item in required_datasets} >= {"openwebtext", "c4_en", "fineweb"}
    assert all(item["target_bpe_tokens"] >= 500_000_000 for item in required_datasets)
    assert all(item["no_fallback_required"] is True for item in required_datasets)
    assert data["strong_target"]["tokens_per_dataset"] >= 1_000_000_000

    budget = _load("token_budget.yaml")
    assert budget["minimum"]["tokens_per_dataset"] == 500_000_000
    assert budget["minimum"]["datasets_required"] >= 3
    assert "whitespace_proxy" in budget["disallowed_counters"]


def test_level3_tokenizer_model_and_training_protocol() -> None:
    tokenizers = {item["tokenizer_id"]: item for item in _load("tokenizers.yaml")["tokenizers"]}
    assert tokenizers["gpt2"]["mainline_allowed"] is True
    assert tokenizers["bpe16k"]["mainline_allowed"] is True
    assert tokenizers["bpe32k"]["mainline_allowed"] is True
    assert tokenizers["char_legacy"]["mainline_allowed"] is False
    assert tokenizers["lightweight_bpe_smoke"]["mainline_allowed"] is False

    models = {item["scale_id"]: item for item in _load("model_matrix.yaml")["model_scales"]}
    assert {"small", "medium", "large_lite"}.issubset(models)
    assert models["tiny_smoke"]["level3_evidence"] is False

    training = _load("training_matrix.yaml")
    assert len(training["minimum_requirements"]["default_seeds"]) >= 3
    assert training["minimum_requirements"]["medium_completed"] is True
    assert "write_ppl_result" in training["forbidden_in_step10A"]


def test_level3_filter_evaluation_mechanism_statistics_protocol() -> None:
    methods = {item["method_id"] for item in _load("filter_matrix.yaml")["methods"]}
    assert {
        "raw",
        "random_same_keep_rate",
        "exact_dedup",
        "minhash_near_dedup",
        "length_filter",
        "c4_style_heuristic_proxy",
        "gopher_style_heuristic_proxy",
        "ccnet_style_proxy",
        "perplexity_filter",
        "classifier_quality_proxy",
        "embedding_diversity_selector",
        "hdqspp_historical",
        "urd_fixed",
        "urd_pareto",
        "urd_ablation_no_utility",
        "urd_ablation_no_risk",
        "urd_ablation_no_diversity",
        "urd_ablation_no_shift",
        "urd_ablation_no_cost",
    }.issubset(methods)

    evaluation = _load("evaluation_matrix.yaml")
    assert {"lm_validation_ppl", "downstream", "risk", "diversity", "cost", "pareto", "statistics"}.issubset(evaluation["metrics"])
    assert evaluation["minimum_downstream_benchmarks"] >= 3
    assert evaluation["official_downstream_completed_in_step10A"] is False

    mechanisms = set(_load("mechanism_matrix.yaml")["analyses"])
    assert {"proxy_utility_mismatch", "overfiltering", "diversity_loss", "domain_shift", "rank_stability", "tokenizer_sensitivity", "scale_trend", "failure_taxonomy"}.issubset(mechanisms)

    stats = _load("statistics_protocol.yaml")["rules"]
    assert stats["n_equals_1_significance_claim_allowed"] is False
    assert stats["ci_crosses_zero_blocks_improvement_claim"] is True

