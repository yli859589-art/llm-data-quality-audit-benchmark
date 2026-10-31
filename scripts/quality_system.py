"""Unified command-line interface for the local data-quality curation system."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quality_system.service import QualitySystemService


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="project root; defaults to this checkout"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "overview", help="show datasets, task summary, device, and missing-real-data warning"
    )
    preflight = sub.add_parser("preflight", help="run protected P0 metadata/full preflight")
    preflight.add_argument("--mode", choices=["metadata", "full"], default="metadata")
    check = sub.add_parser(
        "check", help="inspect JSONL/JSONL.GZ/Parquet file structure and SHA-256"
    )
    check.add_argument("path")
    imp = sub.add_parser("import", help="register a local dataset after an actual scan")
    imp.add_argument("dataset_id")
    imp.add_argument("path")
    imp.add_argument("--source", default="local")
    imp.add_argument("--version", default="")
    analyze = sub.add_parser("analyze", help="compute bounded-sample quality statistics")
    analyze.add_argument("dataset_id")
    analyze.add_argument("--sample-limit", type=int, default=10000)
    sub.add_parser("strategies", help="list filter strategies and their evidence boundaries")
    config_save = sub.add_parser("config-save", help="validate and save a filter config")
    config_save.add_argument("name")
    config_save.add_argument("payload_json")
    config_load = sub.add_parser("config-load", help="load a validated saved filter config")
    config_load.add_argument("name")
    run = sub.add_parser("run", help="launch a detached, persistent filter task")
    run.add_argument("dataset_id")
    run.add_argument(
        "strategy",
        choices=sorted(__import__("quality_system.service", fromlist=["STRATEGIES"]).STRATEGIES),
    )
    run.add_argument("--task-id", default="")
    run.add_argument("--target-keep-rate", type=float)
    run.add_argument("--token-budget", type=int)
    run.add_argument("--max-documents", type=int, default=100000)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--batch-size", type=int, default=1000)
    run.add_argument("--params-json", default="{}")
    sub.add_parser("tasks", help="list persistent task states")
    status = sub.add_parser("status", help="show one task state")
    status.add_argument("task_id")
    resume = sub.add_parser("resume", help="execute a queued/failed task in this process")
    resume.add_argument("task_id")
    cancel = sub.add_parser("cancel", help="request task cancellation")
    cancel.add_argument("task_id")
    export = sub.add_parser(
        "export", help="export a completed task's actual output directory as ZIP"
    )
    export.add_argument("task_id")
    export.add_argument("--name")
    evaluate = sub.add_parser(
        "evaluate-smoke", help="invoke the existing Step 7 LM smoke evaluator"
    )
    evaluate.add_argument("training_manifest")
    evaluate.add_argument("--name", default="lm-smoke")
    args = parser.parse_args()
    service = QualitySystemService(args.root)
    if args.command == "overview":
        _print(service.overview())
    elif args.command == "preflight":
        _print(service.preflight(mode=args.mode))
    elif args.command == "check":
        _print(service.inspect_file(args.path))
    elif args.command == "import":
        _print(
            service.import_dataset(
                args.dataset_id, args.path, source=args.source, version=args.version
            )
        )
    elif args.command == "analyze":
        _print(service.analyze(args.dataset_id, sample_limit=args.sample_limit))
    elif args.command == "strategies":
        _print(service.strategies())
    elif args.command == "config-save":
        try:
            payload = json.loads(args.payload_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"payload_json must be JSON: {exc}") from exc
        _print({"path": str(service.save_config(args.name, payload))})
    elif args.command == "config-load":
        _print(service.load_config(args.name))
    elif args.command == "tasks":
        _print(service.task_list())
    elif args.command == "status":
        _print(service.task(args.task_id))
    elif args.command == "resume":
        _print(service.execute_task(args.task_id))
    elif args.command == "cancel":
        _print(service.cancel_task(args.task_id))
    elif args.command == "export":
        _print({"archive": str(service.export_task(args.task_id, archive_name=args.name))})
    elif args.command == "evaluate-smoke":
        _print(service.evaluate_smoke_training(args.training_manifest, name=args.name))
    elif args.command == "run":
        try:
            params = json.loads(args.params_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--params-json must be JSON: {exc}") from exc
        if not isinstance(params, dict):
            raise SystemExit("--params-json must be an object")
        _print(
            service.start_task(
                {
                    "task_id": args.task_id,
                    "dataset_id": args.dataset_id,
                    "strategy": args.strategy,
                    "target_keep_rate": args.target_keep_rate,
                    "token_budget": args.token_budget,
                    "max_documents": args.max_documents,
                    "seed": args.seed,
                    "batch_size": args.batch_size,
                    "params": params,
                    "allow_proxy": True,
                }
            )
        )


if __name__ == "__main__":
    main()
