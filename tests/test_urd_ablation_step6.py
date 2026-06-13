from __future__ import annotations

import json
from pathlib import Path

from filters_v2.base import FilterConfig
from filters_v2.io import load_filter_inputs
from filters_v2.urd_selector import URDSelectorFilter


def test_urd_ablation_config_disables_intended_component(tmp_path: Path) -> None:
    records = load_filter_inputs("artifacts/data_step2/wikitext2_smoke/train.jsonl")
    filter_instance = URDSelectorFilter(
        FilterConfig(
            filter_name="urd_ablation_no_risk",
            filter_type="urd_selector",
            target_keep_rate=0.5,
            scope="smoke",
            dataset_name="WikiText-2",
            dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
            tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
            allow_proxy=True,
            smoke_only=True,
            params={"disabled_components": ["risk"]},
        )
    )

    filter_instance.filter(records)
    manifest = filter_instance.write_outputs(tmp_path / "urd_ablation_no_risk", root=Path.cwd())
    first_row = json.loads(
        (tmp_path / "urd_ablation_no_risk" / "component_scores.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert manifest["disabled_components"] == ["risk"]
    assert first_row["risk_score"] == 0.0
    assert first_row["risk_components"]["disabled_by_ablation"] is True
