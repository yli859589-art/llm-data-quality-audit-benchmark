from __future__ import annotations

from pathlib import Path

from filters_v2.base import FilterConfig
from filters_v2.io import load_filter_inputs
from filters_v2.urd_selector import URDSelectorFilter
from filters_v2.validation import validate_filter_manifest


def _config(name: str, **params) -> FilterConfig:
    return FilterConfig(
        filter_name=name,
        filter_type="urd_selector",
        target_keep_rate=0.5,
        seed=42,
        scope="smoke",
        dataset_name="WikiText-2",
        dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
        tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
        allow_proxy=True,
        smoke_only=True,
        params=params,
    )


def test_fixed_weight_urd_produces_decisions_and_outputs(tmp_path: Path) -> None:
    records = load_filter_inputs("artifacts/data_step2/wikitext2_smoke/train.jsonl")
    filter_instance = URDSelectorFilter(_config("urd_fixed", selection_mode="fixed_weight"))
    result = filter_instance.filter(records)
    manifest = filter_instance.write_outputs(tmp_path / "urd_fixed", root=Path.cwd())

    validate_filter_manifest(manifest, Path.cwd())

    assert result.kept_docs == 2
    assert manifest["method_family"] == "URD-Selector"
    assert manifest["selection_mode"] == "fixed_weight"
    assert manifest["verified_effectiveness"] is False
    assert (tmp_path / "urd_fixed" / "component_scores.jsonl").exists()
    assert (tmp_path / "urd_fixed" / "urd_summary.json").exists()
