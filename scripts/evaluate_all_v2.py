from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path
from typing import Callable

from evaluation_v2.base import EvaluationConfig
from evaluation_v2.cost_eval import run_cost_evaluation
from evaluation_v2.diversity_eval import run_diversity_evaluation
from evaluation_v2.downstream import run_downstream_protocol
from evaluation_v2.lm_metrics import run_lm_evaluation
from evaluation_v2.pareto import run_pareto_evaluation
from evaluation_v2.risk_eval import run_risk_evaluation
from evaluation_v2.schema import PROTOCOL_SCOPES
from evaluation_v2.stability import run_stability_evaluation
from experiment_utils import root


RUNNERS: dict[str, Callable] = {
    "lm": run_lm_evaluation,
    "risk": run_risk_evaluation,
    "diversity": run_diversity_evaluation,
    "cost": run_cost_evaluation,
    "pareto": run_pareto_evaluation,
    "downstream_protocol": run_downstream_protocol,
    "stability": run_stability_evaluation,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 7 evaluation_v2 smoke/protocol evaluators.")
    parser.add_argument("--evaluation", required=True, choices=sorted(RUNNERS))
    parser.add_argument("--input-artifact", default="")
    parser.add_argument("--input-manifest", default="")
    parser.add_argument("--training-manifest", default="")
    parser.add_argument("--filter-manifest", default="")
    parser.add_argument("--tokenizer-manifest", default="")
    parser.add_argument("--method-name", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--allow-smoke", action="store_true")
    parser.add_argument("--allow-protocol", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-samples", type=int, default=200)
    return parser.parse_args()


def _config_from_args(args: argparse.Namespace) -> EvaluationConfig:
    if args.scope == "smoke" and not args.allow_smoke:
        raise SystemExit("Smoke evaluation requires --allow-smoke")
    if args.scope in PROTOCOL_SCOPES and not args.allow_protocol:
        raise SystemExit("Protocol evaluation requires --allow-protocol")
    if args.scope == "completed_run" and not any([args.input_artifact, args.training_manifest, args.filter_manifest]):
        raise SystemExit("completed_run requires a real input artifact")
    payload = {
        "evaluation_name": Path(args.output_dir).name,
        "evaluation_type": args.evaluation,
        "scope": args.scope,
        "method_name": args.method_name,
        "dataset_name": args.dataset_name,
        "input_artifact_path": args.input_artifact,
        "input_manifest_path": args.input_manifest,
        "training_manifest_path": args.training_manifest,
        "filter_manifest_path": args.filter_manifest,
        "tokenizer_manifest_path": args.tokenizer_manifest,
        "seed": args.seed,
        "bootstrap_samples": args.bootstrap_samples,
        "smoke_only": args.scope == "smoke",
        "protocol_only": args.scope in PROTOCOL_SCOPES,
        "notes": "Step 7 evaluation output; not main evidence.",
    }
    return EvaluationConfig.from_mapping(payload)


def main() -> None:
    args = _parse_args()
    config = _config_from_args(args)
    output_dir = root / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    result = RUNNERS[args.evaluation](config, output_dir, root)
    print(
        json.dumps(
            {
                "status": "completed" if result.completed else "protocol_only",
                "evaluation": args.evaluation,
                "scope": config.scope,
                "smoke_only": config.smoke_only,
                "protocol_only": config.protocol_only,
                "output_dir": args.output_dir,
                "manifest_path": (output_dir / "evaluation_manifest.json").relative_to(root).as_posix()
                if (output_dir / "evaluation_manifest.json").is_relative_to(root)
                else (output_dir / "evaluation_manifest.json").as_posix(),
                "effectiveness_claim_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
