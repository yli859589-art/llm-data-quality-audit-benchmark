from __future__ import annotations

import json
from pathlib import Path

from filters_v2.base import FilterConfig
from filters_v2.io import load_filter_inputs
from filters_v2.urd_selector import URDSelectorFilter


def test_pareto_urd_outputs_frontier_and_layers(tmp_path: Path) -> None:
    records = load_filter_inputs("artifacts/data_step2/wikitext2_smoke/train.jsonl")
    filter_instance = URDSelectorFilter(
        FilterConfig(
            filter_name="urd_pareto",
            filter_type="urd_selector",
            target_keep_rate=0.5,
            scope="smoke",
            dataset_name="WikiText-2",
            dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
            tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
            allow_proxy=True,
            smoke_only=True,
            params={"selection_mode": "pareto"},
        )
    )

    result = filter_instance.filter(records)
    manifest = filter_instance.write_outputs(tmp_path / "urd_pareto", root=Path.cwd())
    layers = json.loads((tmp_path / "urd_pareto" / "pareto_layers.json").read_text(encoding="utf-8"))

    assert result.kept_docs == 2
    assert manifest["selection_mode"] == "pareto"
    assert manifest["pareto_proxy_used"] is True
    assert (tmp_path / "urd_pareto" / "pareto_frontier.csv").exists()
    assert layers["layers"]
