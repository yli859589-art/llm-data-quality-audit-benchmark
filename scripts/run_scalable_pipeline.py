"""Run the P1-2 resumable shard processor without mutating historical artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data.scalable_pipeline import PipelineConfig, run_resumable_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="JSONL, JSONL.GZ, or Parquet shard; repeatable",
    )
    parser.add_argument("--task-id", required=True)
    parser.add_argument(
        "--output-dir",
        required=True,
        help="New versioned output directory (for example artifacts/p1_02/<run>)",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--config-identity", default="")
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    historical = (ROOT / "artifacts" / "evaluation_step7").resolve()
    if output == historical or historical in output.parents:
        raise ValueError("refusing to write a historical evidence directory")
    config = PipelineConfig(
        args.task_id,
        tuple(args.input),
        str(output),
        args.batch_size,
        config_identity=args.config_identity,
    )
    manifest = run_resumable_pipeline(config, lambda row: row)
    print(
        f"completed: {manifest['processed_shards']} processed, {manifest['skipped_shards']} resumed"
    )
    print(output / "pipeline_manifest.json")


if __name__ == "__main__":
    main()
