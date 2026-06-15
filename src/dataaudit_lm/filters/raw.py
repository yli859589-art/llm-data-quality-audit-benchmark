from __future__ import annotations

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest


def apply_raw_filter(records: list[DataRecord]) -> FilterResult:
    decisions = [
        FilterDecision(record_id=record.record_id, kept=True, reason="raw_retains_all_records")
        for record in sorted(records, key=lambda item: item.record_id)
    ]
    kept = [record for record in sorted(records, key=lambda item: item.record_id)]
    manifest = build_filter_manifest(
        method_name="raw",
        records=records,
        decisions=decisions,
        parameters={"raw_ingestion_policy": "retain_all_upstream_records_no_content_dedup"},
    )
    return FilterResult("raw", len(records), kept, decisions, manifest)
