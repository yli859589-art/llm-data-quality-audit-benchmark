from __future__ import annotations

from dataaudit_lm.data.records import make_record
from dataaudit_lm.data.splitting import cluster_aware_hash_split


def _records():
    return [
        make_record(
            record_id="a",
            source_row_id="0",
            text="same text",
            source_dataset="toy",
            source_revision="r1",
        ),
        make_record(
            record_id="b",
            source_row_id="1",
            text="same text",
            source_dataset="toy",
            source_revision="r1",
        ),
        make_record(
            record_id="c",
            source_row_id="2",
            text="different text",
            source_dataset="toy",
            source_revision="r1",
        ),
    ]


def test_cluster_split_is_order_invariant_and_keeps_duplicates_together() -> None:
    left, manifest_left = cluster_aware_hash_split(_records(), seed=7)
    right, manifest_right = cluster_aware_hash_split(list(reversed(_records())), seed=7)

    assert manifest_left.manifest_hash == manifest_right.manifest_hash
    assert {name: [row.record_id for row in rows] for name, rows in left.items()} == {
        name: [row.record_id for row in rows] for name, rows in right.items()
    }
    split_by_id = {row.record_id: split for split, rows in left.items() for row in rows}
    assert split_by_id["a"] == split_by_id["b"]
    assert manifest_left.cluster_cross_split_violations == 0
