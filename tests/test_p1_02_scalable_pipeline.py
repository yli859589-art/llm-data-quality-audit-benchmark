from __future__ import annotations

import json
import gzip
from pathlib import Path

import pytest

from data.scalable_pipeline import PipelineConfig, run_resumable_pipeline
from data.split_audit import audit_split_duplicates
from data.cross_shard_dedup import index_cross_shard_records, write_dedup_decisions
from filters_v2.persistent_minhash import PersistentMinHashIndex
from training_v2.streaming_sampler import StreamingShardSampler


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_resumable_shard_processing_matches_uninterrupted_and_blocks_config_change(
    tmp_path: Path,
) -> None:
    first, second = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    _write(first, [{"id": "a", "text": "one"}, {"id": "b", "text": "two"}])
    _write(second, [{"id": "c", "text": "three"}])
    transform = lambda row: {**row, "kept": True}
    config = PipelineConfig(
        "fixture", (str(first), str(second)), str(tmp_path / "resumed"), batch_size=1
    )
    with pytest.raises(RuntimeError, match="simulated interruption"):
        run_resumable_pipeline(config, transform, fail_after_shards=1)
    resumed = run_resumable_pipeline(config, transform)
    clean = run_resumable_pipeline(
        PipelineConfig(
            "fixture-clean", (str(first), str(second)), str(tmp_path / "clean"), batch_size=1
        ),
        transform,
    )
    assert resumed["rows_out"] == 1  # only the newly processed second shard
    assert clean["rows_out"] == 3
    assert sum(1 for _ in (tmp_path / "resumed").glob("shard-*.jsonl")) == 2
    with pytest.raises(ValueError, match="configuration"):
        run_resumable_pipeline(
            PipelineConfig(
                "fixture", (str(first), str(second)), str(tmp_path / "resumed"), batch_size=2
            ),
            transform,
        )
    _write(second, [{"id": "c", "text": "changed"}])
    with pytest.raises(ValueError, match="configuration"):
        run_resumable_pipeline(config, transform)


def test_persistent_lsh_detects_cross_shard_duplicate_without_all_pairs(tmp_path: Path) -> None:
    index = PersistentMinHashIndex(
        tmp_path / "index.sqlite", shingle_size=2, permutations=32, bands=8, seed=9
    )
    records = [
        {
            "id": "train-1",
            "split": "train",
            "text": "a detailed article about reproducible language model training",
            "gpt2_tokens": 8,
        },
        {
            "id": "valid-1",
            "split": "valid",
            "text": "a detailed article about reproducible language model training",
            "gpt2_tokens": 8,
        },
        {
            "id": "test-1",
            "split": "test",
            "text": "unrelated astronomy observation report with measured values",
            "gpt2_tokens": 7,
        },
    ]
    report = audit_split_duplicates(records, index, threshold=0.9)
    index.close()
    assert report["exact_cross_split_documents"] == 2
    assert report["near_duplicate_pair_count"] >= 1
    assert report["mode"] == "audit_only_no_deletion"


def test_gzip_reader_and_disk_backed_sampler_are_input_order_independent(tmp_path: Path) -> None:
    first, second = tmp_path / "one.jsonl.gz", tmp_path / "two.jsonl"
    with gzip.open(first, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": "b", "text": "two words", "gpt2_tokens": 2}) + "\n")
    _write(
        second,
        [
            {"id": "a", "text": "one", "gpt2_tokens": 1},
            {"id": "c", "text": "three four", "gpt2_tokens": 2},
        ],
    )
    sampler = StreamingShardSampler(
        tmp_path / "sampler.sqlite", shard_paths=(str(first), str(second)), seed=7
    )
    assert sampler.build_index(lambda row: int(row["gpt2_tokens"])) == {
        "documents": 3,
        "tokens": 5,
        "reused_index": 0,
    }
    selected = sampler.select_ids(3)
    reversed_sampler = StreamingShardSampler(
        tmp_path / "other.sqlite", shard_paths=(str(second), str(first)), seed=7
    )
    reversed_sampler.build_index(lambda row: int(row["gpt2_tokens"]))
    assert selected == reversed_sampler.select_ids(3)
    assert sum(1 for _ in sampler.iter_selected_records(selected)) == len(selected)
    sampler.close()
    reversed_sampler.close()


def test_persistent_clusters_use_stable_representative(tmp_path: Path) -> None:
    index = PersistentMinHashIndex(
        tmp_path / "clusters.sqlite", shingle_size=2, permutations=32, bands=8, seed=4
    )
    text = "stable deterministic representative for duplicate documents"
    assert index.add_and_cluster("z-doc", text, "train", threshold=0.9) == "z-doc"
    assert index.add_and_cluster("a-doc", text, "valid", threshold=0.9) == "a-doc"
    index.commit()
    assert index.cluster_representatives() == {"a-doc": "a-doc", "z-doc": "a-doc"}
    index.close()


def test_failure_writes_a_manifest_and_keeps_no_partial_output(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    _write(source, [{"id": "x", "text": "will fail"}])
    output = tmp_path / "failure"
    with pytest.raises(ZeroDivisionError):
        run_resumable_pipeline(
            PipelineConfig("failure", (str(source),), str(output)), lambda row: 1 / 0
        )
    manifest = json.loads((output / "pipeline_manifest.json").read_text(encoding="utf-8"))
    assert manifest["errors"][0]["shard"] == str(source)
    assert not list(output.glob("*.tmp"))


def test_cross_shard_dedup_emits_deterministic_cluster_decisions(tmp_path: Path) -> None:
    left, right = tmp_path / "left.jsonl", tmp_path / "right.jsonl"
    _write(left, [{"id": "z", "text": "shared duplicate content appears here"}])
    _write(
        right,
        [
            {"id": "a", "text": "shared duplicate content appears here"},
            {"id": "m", "text": "independent material"},
        ],
    )
    index = PersistentMinHashIndex(
        tmp_path / "dedup.sqlite", shingle_size=2, permutations=32, bands=8
    )
    assert (
        index_cross_shard_records((str(left), str(right)), index, threshold=0.9)["duplicates"] == 1
    )
    assert write_dedup_decisions(index, tmp_path / "decisions.jsonl") == {"documents": 3, "kept": 2}
    rows = [
        json.loads(line)
        for line in (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0] == {"id": "a", "keep": True, "representative_id": "a"}
    assert rows[-1] == {"id": "z", "keep": False, "representative_id": "a"}
    index.close()
