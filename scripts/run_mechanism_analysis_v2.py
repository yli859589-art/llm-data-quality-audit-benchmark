from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path
from typing import Callable

from analysis_v2.base import MechanismAnalysisConfig
from analysis_v2.diversity_loss import run_diversity_loss_analysis
from analysis_v2.domain_shift import run_domain_shift_analysis
from analysis_v2.failure_taxonomy import run_failure_taxonomy_analysis
from analysis_v2.overfiltering import run_overfiltering_analysis
from analysis_v2.pareto_mechanism import run_pareto_mechanism_analysis
from analysis_v2.proxy_utility import run_proxy_utility_analysis
from analysis_v2.rank_stability import run_rank_stability_analysis
from analysis_v2.scale_trend import run_scale_trend_analysis
from analysis_v2.schema import PROTOCOL_SCOPES
from analysis_v2.tokenizer_sensitivity import run_tokenizer_sensitivity_analysis
from experiment_utils import root


RUNNERS: dict[str, Callable] = {
    "proxy_utility": run_proxy_utility_analysis,
    "overfiltering": run_overfiltering_analysis,
    "diversity_loss": run_diversity_loss_analysis,
    "domain_shift": run_domain_shift_analysis,
    "rank_stability": run_rank_stability_analysis,
    "tokenizer_sensitivity": run_tokenizer_sensitivity_analysis,
    "scale_trend": run_scale_trend_analysis,
    "failure_taxonomy": run_failure_taxonomy_analysis,
    "pareto_mechanism": run_pareto_mechanism_analysis,
    "combined_smoke": run_failure_taxonomy_analysis,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 8 mechanism-analysis smoke/protocol analyzers.")
    parser.add_argument("--analysis", required=True, choices=sorted(RUNNERS))
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--method-name", action="append", required=True)
    parser.add_argument("--input-artifact", action="append", default=[])
    parser.add_argument("--input-manifest", action="append", default=[])
    parser.add_argument("--filter-manifest", action="append", default=[])
    parser.add_argument("--training-manifest", action="append", default=[])
    parser.add_argument("--evaluation-manifest", action="append", default=[])
    parser.add_argument("--tokenizer-manifest", action="append", default=[])
    parser.add_argument("--scope", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--allow-smoke", action="store_true")
    parser.add_argument("--allow-protocol", action="store_true")
    return parser.parse_args()


def _config_from_args(args: argparse.Namespace) -> MechanismAnalysisConfig:
    if args.scope == "smoke" and not args.allow_smoke:
        raise SystemExit("Smoke mechanism analysis requires --allow-smoke")
    if args.scope in PROTOCOL_SCOPES and not args.allow_protocol:
        raise SystemExit("Protocol mechanism analysis requires --allow-protocol")
    if args.scope == "completed_run" and not any(
        [args.input_artifact, args.input_manifest, args.filter_manifest, args.evaluation_manifest]
    ):
        raise SystemExit("completed_run requires real input artifacts")
    payload = {
        "analysis_name": Path(args.output_dir).name,
        "analysis_type": "combined" if args.analysis == "combined_smoke" else args.analysis,
        "scope": args.scope,
        "dataset_name": args.dataset_name,
        "methods": args.method_name,
        "input_artifact_paths": args.input_artifact,
        "input_manifest_paths": args.input_manifest,
        "training_manifest_paths": args.training_manifest,
        "filter_manifest_paths": args.filter_manifest,
        "evaluation_manifest_paths": args.evaluation_manifest,
        "tokenizer_manifest_paths": args.tokenizer_manifest,
        "output_dir": args.output_dir,
        "smoke_only": args.scope == "smoke",
        "protocol_only": args.scope in PROTOCOL_SCOPES,
        "insufficient_evidence_policy": "mark_explicitly",
        "notes": "Step 8 mechanism-analysis output; not main evidence.",
    }
    return MechanismAnalysisConfig.from_mapping(payload)


def main() -> None:
    args = _parse_args()
    config = _config_from_args(args)
    output_dir = root / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    result = RUNNERS[args.analysis](config, output_dir, root)
    manifest_path = output_dir / "mechanism_manifest.json"
    try:
        manifest_label = manifest_path.relative_to(root).as_posix()
    except ValueError:
        manifest_label = manifest_path.as_posix()
    print(
        json.dumps(
            {
                "status": "completed" if not config.protocol_only else "protocol_only",
                "analysis": args.analysis,
                "scope": config.scope,
                "smoke_only": config.smoke_only,
                "protocol_only": config.protocol_only,
                "output_dir": args.output_dir,
                "manifest_path": manifest_label,
                "evidence_sufficiency": result.evidence_sufficiency,
                "insufficient_evidence": result.insufficient_evidence,
                "claim_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

