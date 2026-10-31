"""Generate a reproducible MinHash/LSH scaling report on synthetic shard metadata."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from filters_v2.persistent_minhash import PersistentMinHashIndex


def benchmark(documents: int) -> dict[str, int | float]:
    with tempfile.TemporaryDirectory(prefix="p1-02-minhash-") as directory:
        index = PersistentMinHashIndex(
            Path(directory) / "index.sqlite", shingle_size=3, permutations=64, bands=16, seed=42
        )
        tracemalloc.start()
        started = time.perf_counter()
        for number in range(documents):
            # Distinct, fixed-length text avoids a quadratic all-pairs workload.
            index.add_and_cluster(
                f"doc-{number:06d}",
                f"benchmark document {number} unique payload {number * 7919}",
                "train",
                threshold=0.9,
            )
        index.commit()
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        candidates, _ = index.candidates("benchmark document 1 unique payload 7919")
        profile = index.profile_snapshot()
        index.close()
    return {
        "documents": documents,
        "elapsed_seconds": elapsed,
        "documents_per_second": documents / elapsed,
        "peak_tracemalloc_bytes": peak,
        "probe_candidates": len(candidates),
        "all_pairs": documents * (documents - 1) // 2,
        "profile": profile,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--sizes", nargs="+", type=int, default=[300, 3000, 30000])
    args = parser.parse_args()
    results = [benchmark(size) for size in args.sizes]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"benchmark": "p1-02 persistent MinHash/LSH", "results": results}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
