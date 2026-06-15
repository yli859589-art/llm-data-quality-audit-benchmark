from __future__ import annotations

from dataaudit_lm.data.sources import SourceSpec, ingest_rows_without_dedup
from dataaudit_lm.filters.raw import apply_raw_filter


def test_raw_ingestion_retains_true_duplicate_content() -> None:
    records = ingest_rows_without_dedup(
        SourceSpec("toy_repo", "default", "rev1"),
        [{"id": "0", "text": "duplicate"}, {"id": "1", "text": "duplicate"}],
    )
    result = apply_raw_filter(records)

    assert len(records) == 2
    assert records[0].content_sha256 == records[1].content_sha256
    assert result.kept_ids == [records[0].record_id, records[1].record_id]
    assert result.manifest["input_count"] == 2
    assert result.manifest["kept_count"] == 2
