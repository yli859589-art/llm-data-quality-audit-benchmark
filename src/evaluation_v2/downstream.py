from __future__ import annotations

from pathlib import Path

from .base import EvaluationConfig, EvaluationResult
from .io import write_json, write_text
from .manifest import create_evaluation_manifest, write_manifest


BENCHMARKS = [
    "LAMBADA",
    "PIQA",
    "HellaSwag",
    "ARC-Easy",
    "BoolQ",
    "Winogrande",
    "tiny_local_classification_smoke",
    "tiny_local_language_understanding_smoke",
]


def run_downstream_protocol(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    rows = [
        {
            "benchmark": name,
            "artifact_available": False,
            "download_attempted": False,
            "completed": False,
            "protocol_only": True,
            "notes": "No external benchmark is downloaded in Step 7.",
        }
        for name in BENCHMARKS
    ]
    metrics = {
        "downstream_protocol_matrix": rows,
        "official_downstream_completed": False,
        "tiny_local_smoke_completed": False,
        "protocol_only": True,
        "effectiveness_claim_allowed": False,
        "main_evidence": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "downstream_protocol_matrix.json"
    report_path = output_dir / "downstream_evaluation_report.md"
    write_json(metrics_path, metrics)
    write_text(
        report_path,
        "# Downstream Protocol\n\n"
        "Step 7 records the downstream benchmark protocol only. No official downstream benchmark "
        "is completed, no external benchmark is downloaded, and no downstream improvement claim is allowed.\n",
    )
    manifest = create_evaluation_manifest(
        config=config,
        root=root,
        metrics_path=metrics_path,
        report_path=report_path,
        completed=False,
        notes="Downstream protocol only; no completed benchmark result.",
    )
    write_manifest(output_dir / "evaluation_manifest.json", manifest)
    return EvaluationResult(config.evaluation_name, config.evaluation_type, config.method_name, config.dataset_name, config.scope, metrics, {"official_downstream_completed": False}, {}, {"metrics": metrics_path.as_posix(), "report": report_path.as_posix()}, config.smoke_only, config.protocol_only, False, "Protocol only.")
