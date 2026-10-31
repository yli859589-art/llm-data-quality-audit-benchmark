# P1-2 scalable processing and runtime verification

## Scope and evidence boundary

This upgrade adds new P1-2 processing capabilities only.  It does not alter
historical evaluation artifacts, result tables, or claims.  The nine declared
formal corpus shards are absent from this checkout, so no real-data training or
benchmark claim is made here.  Fixture tests establish behavior; real-data
results require separately supplied, checksum-verified shards.

## Implemented pipeline

- `data.scalable_pipeline` streams JSONL, JSONL.GZ, and (when `pyarrow` is
  installed) Parquet row groups.  Each output shard is written to a temporary
  file and atomically replaced only after the whole source shard succeeds.
- `resume.sqlite` records each input/output SHA-256, row counts, and completed
  status.  It rejects continuation if input content, input list, batch size,
  pipeline version, or caller-provided configuration identity changes.
- A manifest records rows, rate, traced peak allocation, output shard paths,
  and any failure.  Partial files are removed and the exception is re-raised.
- `scripts/run_scalable_pipeline.py` is the command-line entry point.  New
  outputs should use a versioned directory such as
  `artifacts/p1_02/<run-id>/`; it refuses the historical evidence directory.

## Cross-shard quality and splits

- `PersistentMinHashIndex` keeps MinHash/LSH bands and shingle evidence in
  SQLite.  Candidate selection is LSH-based and confirmation uses exact shingle
  Jaccard, avoiding all-pairs comparison.
- `add_and_cluster` makes the smallest document ID the representative of a
  connected duplicate cluster, including when a smaller ID arrives later.
- `data.cross_shard_dedup` indexes all shards before it writes decisions, then
  emits an explicit deterministic keep/representative record per document.
- `audit_split_duplicates` is audit-only: it reports exact and near duplicate
  cross-split groups, token totals, and ID conflicts and never deletes records.

## Training-data sampling and acquisition

- `StreamingShardSampler` first writes document metadata (ID, shard ordinal,
  token count, stable rank) to SQLite, then rereads only selected records.  The
  selection is a seed-derived SHA-256 ranking over the entire pool, not a file
  prefix; input order does not affect the selected ID set.
- `scripts/fetch_p1_02_shard.py` is manifest-first and defaults to `--plan`.
  A network transfer needs explicit `--execute`, supports byte-range resume,
  and rejects a completed shard unless its declared SHA-256 matches.  No large
  download was initiated during this upgrade.

## Verification performed

`python -m pytest tests/test_p1_02_scalable_pipeline.py -q` passed: 6 tests
cover interruption/restart, changed-configuration blocking, JSONL.GZ streaming,
disk-backed sampling, cross-split duplicate audit, deterministic cluster
representatives, persistent cross-shard decisions, and durable failure
reporting.

Persistent-index measurements are stored only in the ignored new report
directory `artifacts/upgrade_reports/p1-02/`: 300 synthetic documents completed
in 0.748 s, 3,000 in 33.294 s, and 30,000 in 428.664 s (69.98 documents/s),
all with tracemalloc enabled.  A separately launched 30,000-document repeat
completed in 353.959 s (84.76 documents/s); both records are retained rather
than selecting a favorable value.  Each probe returned one LSH candidate instead
of enumerating 44,850, 4,498,500, and 449,985,000 possible pairs respectively.
These are synthetic indexing measurements, not real-corpus quality or training
results.
