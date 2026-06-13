from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Level3Plan:
    stage: str
    purpose: str
    planned_commands: list[str]
    expected_artifacts: list[str]
    required_resources: list[str]
    readiness_impact: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "step": "step10A_level3_heavy_protocol_freeze",
            "stage": self.stage,
            "purpose": self.purpose,
            "dry_run": True,
            "protocol_only": True,
            "completed": False,
            "executed": False,
            "not_executed_reason": "Heavy jobs are not executed in Step 10A.",
            "planned_commands": self.planned_commands,
            "expected_artifacts": self.expected_artifacts,
            "required_resources": self.required_resources,
            "readiness_impact": self.readiness_impact,
        }


PLANS: dict[str, Level3Plan] = {
    "data": Level3Plan(
        stage="data",
        purpose="Prepare at least three no-fallback 500M-token BPE-counted corpora.",
        planned_commands=[
            "python scripts/prepare_data_v2.py --config configs/level3/data_matrix.yaml --dataset openwebtext --target-bpe-tokens 500000000",
            "python scripts/prepare_data_v2.py --config configs/level3/data_matrix.yaml --dataset c4_en --target-bpe-tokens 500000000",
            "python scripts/prepare_data_v2.py --config configs/level3/data_matrix.yaml --dataset fineweb --target-bpe-tokens 500000000",
            "python scripts/check_dataset_manifests.py --level3",
        ],
        expected_artifacts=[
            "artifacts/level3_data/*/data_manifest.json",
            "artifacts/level3_data/*/split_integrity.json",
            "artifacts/level3_data/*/license_scope.md",
        ],
        required_resources=["multi-TB storage", "network access", "CPU workers"],
        readiness_impact="Can move DataGate toward pass only after real manifests prove no-fallback 500M BPE-token data.",
    ),
    "filters": Level3Plan(
        stage="filters",
        purpose="Run the full baseline and URD filter matrix under matched keep-rate.",
        planned_commands=[
            "python scripts/run_filter_v2.py --config configs/level3/filter_matrix.yaml --dataset <dataset_id>",
            "python scripts/check_filter_manifests.py --level3",
        ],
        expected_artifacts=[
            "artifacts/level3_filters/*/filter_manifest.json",
            "artifacts/level3_filters/*/keep_rate_report.json",
            "artifacts/level3_filters/*/filter_scores.jsonl",
        ],
        required_resources=["prepared Level 3 data", "CPU workers", "disk for filtered corpora"],
        readiness_impact="Can move FilterGate toward pass only after all required methods run on heavy data.",
    ),
    "training": Level3Plan(
        stage="training",
        purpose="Train small and medium models with multi-seed manifests and selected large-lite runs.",
        planned_commands=[
            "python scripts/train_model_v2.py --config configs/level3/training_matrix.yaml --scale small --seeds 13 42 101",
            "python scripts/train_model_v2.py --config configs/level3/training_matrix.yaml --scale medium --seeds 13 42 101",
            "python scripts/train_model_v2.py --config configs/level3/training_matrix.yaml --scale large_lite --selected --seeds 13",
            "python scripts/check_training_manifests.py --level3",
        ],
        expected_artifacts=[
            "artifacts/level3_training/*/training_manifest.json",
            "artifacts/level3_training/*/checkpoint_manifest.json",
            "artifacts/level3_training/*/metrics.jsonl",
            "artifacts/level3_training/*/loss_curve.csv",
        ],
        required_resources=["dedicated GPU", "prepared tokenizer manifests", "multi-day runtime"],
        readiness_impact="Can move ModelScaleGate toward pass only after small/medium and selected large-lite evidence is complete.",
    ),
    "evaluation": Level3Plan(
        stage="evaluation",
        purpose="Evaluate LM, downstream, risk, diversity, cost, stability, and Pareto metrics.",
        planned_commands=[
            "python scripts/evaluate_all_v2.py --config configs/level3/evaluation_matrix.yaml --level3",
            "python scripts/check_evaluation_manifests.py --level3",
        ],
        expected_artifacts=[
            "artifacts/level3_evaluation/*/evaluation_manifest.json",
            "artifacts/level3_tables/main_results_level3.csv",
            "artifacts/level3_tables/downstream_results_level3.csv",
            "artifacts/level3_tables/pareto_frontier_level3.csv",
        ],
        required_resources=["completed checkpoints", "benchmark data access", "GPU/CPU evaluation time"],
        readiness_impact="Can move EvaluationGate toward pass only after official downstream and statistics artifacts are complete.",
    ),
    "analysis": Level3Plan(
        stage="analysis",
        purpose="Run mechanism analysis and failure taxonomy across datasets, tokenizers, and model scales.",
        planned_commands=[
            "python scripts/run_mechanism_analysis_v2.py --config configs/level3/mechanism_matrix.yaml --level3",
            "python scripts/check_mechanism_manifests.py --level3",
        ],
        expected_artifacts=[
            "artifacts/level3_analysis/*/mechanism_manifest.json",
            "artifacts/level3_reports/mechanism_report.md",
            "artifacts/level3_reports/failure_taxonomy.md",
        ],
        required_resources=["Level 3 evaluation tables", "completed filter and training lineage"],
        readiness_impact="Can move MechanismGate toward pass only after full-scale cross-dataset evidence is linked.",
    ),
    "release": Level3Plan(
        stage="release",
        purpose="Freeze Level 3 artifacts, tables, figures, claim map, and release package.",
        planned_commands=[
            "python scripts/check_level3_protocol.py",
            "python scripts/check_level3_preflight.py",
            "python scripts/run_all_checks.py --timeout 300",
            "python scripts/run_release_checks.py --timeout 300",
        ],
        expected_artifacts=[
            "artifacts/level3_release/level3_release_candidate.zip",
            "artifacts/level3_reports/reproducibility.md",
            "artifacts/level3_reports/limitations.md",
        ],
        required_resources=["completed Step 10B evidence", "clean repository tree"],
        readiness_impact="Can support a completed Level 3 release only after data, training, evaluation, and mechanism gates pass.",
    ),
}


def emit_plan(stage: str) -> int:
    parser = argparse.ArgumentParser(description=f"Dry-run Level 3 {stage} plan.")
    parser.add_argument("--execute", action="store_true", help="Blocked in Step 10A.")
    parser.add_argument("--json-out", default="", help="Optional report path.")
    args = parser.parse_args()
    plan = PLANS[stage].to_payload()
    if args.execute:
        plan["blocked"] = True
        plan["blocked_reason"] = "Step 10A freezes protocol only; run Step 10B for heavy execution."
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 2
    if args.json_out:
        out = ROOT / args.json_out if not Path(args.json_out).is_absolute() else Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def main_for(stage: str) -> None:
    raise SystemExit(emit_plan(stage))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in PLANS:
        print("usage: python scripts/level3/plan_utils.py <data|filters|training|evaluation|analysis|release>", file=sys.stderr)
        raise SystemExit(2)
    stage_arg = sys.argv.pop(1)
    main_for(stage_arg)

