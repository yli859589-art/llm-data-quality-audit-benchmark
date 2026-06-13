from __future__ import annotations

import json
from pathlib import Path

from filters_v2.base import FilterConfig
from filters_v2.io import load_filter_inputs
from filters_v2.raw import RawFilter
from filters_v2.validation import validate_filter_manifest


def test_filter_manifest_schema_and_output_hashes_validate(tmp_path: Path) -> None:
    records = load_filter_inputs("artifacts/data_step2/wikitext2_smoke/train.jsonl")
    config = FilterConfig(
        filter_name="raw",
        filter_type="raw",
        scope="smoke",
        dataset_name="WikiText-2",
        dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
        tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
        smoke_only=True,
    )
    filter_instance = RawFilter(config)
    result = filter_instance.filter(records)
    manifest = filter_instance.write_outputs(tmp_path / "raw", root=Path.cwd())

    validate_filter_manifest(manifest, Path.cwd())

    assert manifest["manifest_version"] == "step4.filter_manifest.v1"
    assert manifest["smoke_only"] is True
    assert manifest["proxy_used"] is False
    assert set(manifest["output_hashes"])
    assert json.loads((tmp_path / "raw" / "keep_rate_report.json").read_text(encoding="utf-8"))[
        "document_keep_rate"
    ] == result.document_keep_rate
