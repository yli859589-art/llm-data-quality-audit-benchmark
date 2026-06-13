from __future__ import annotations

from pathlib import Path

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, write_manifest


FAILURE_ROWS = [
    ("proxy_utility_mismatch", "hypothesized", "Filter proxy may not track actual training utility."),
    ("overfiltering", "hypothesized", "Aggressive retention can remove useful tokens."),
    ("diversity_collapse", "hypothesized", "Filtering can reduce lexical or semantic coverage."),
    ("domain_shift", "hypothesized", "Selection can move data away from the validation distribution."),
    ("tokenizer_budget_mismatch", "protocol_only", "Whitespace/char/BPE budgets can disagree."),
    ("weak_baseline_illusion", "protocol_only", "Method gains are unsafe without raw/random/dedup/length controls."),
    ("small_model_artifact", "protocol_only", "Tiny/small behavior may not transfer to larger scales."),
    ("seed_instability", "insufficient_evidence", "Multi-seed evidence is not yet complete."),
    ("smoke_main_leakage_risk", "observed_risk_controlled", "Checks keep smoke/protocol artifacts out of main tables."),
    ("protocol_completed_confusion", "observed_risk_controlled", "Manifests separate protocol_only from completed outputs."),
    ("negative_result_preservation", "observed", "Historical negative results are retained as audit evidence."),
    (
        "hdqspp_historical_failure",
        "observed",
        "HDQS++ v3 did not outperform raw in the current historical fair benchmark evidence.",
    ),
    ("insufficient_evidence_categories", "observed", "Step 8 explicitly marks smoke/protocol findings as insufficient."),
]


def run_failure_taxonomy_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=len(FAILURE_ROWS),
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["Level 2/3 mechanism matrix", "multi-seed evidence", "formal downstream evidence"],
    )
    rows = [
        {
            "failure_type": item[0],
            "evidence_status": item[1],
            "description": item[2],
            "negative_result_preserved": item[0] in {"negative_result_preservation", "hdqspp_historical_failure"},
            "insufficient_evidence": item[1] in {"hypothesized", "protocol_only", "insufficient_evidence"},
        }
        for item in FAILURE_ROWS
    ]
    summary = {
        "failure_categories": len(rows),
        "observed_categories": len([row for row in rows if str(row["evidence_status"]).startswith("observed")]),
        "hdqspp_historical_failure_recorded": True,
        "negative_result_preservation_recorded": True,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "failure_taxonomy_table.csv"
    json_path = output_dir / "failure_taxonomy.json"
    report_path = output_dir / "failure_taxonomy.md"
    write_csv(table_path, rows)
    write_json(json_path, {"summary": summary, "failures": rows})
    lines = [
        "# Failure Taxonomy",
        "",
        "This taxonomy preserves observed, hypothesized, protocol-only, and insufficient-evidence failure modes.",
        "It does not present URD as a method that fixes all failures.",
        "",
        "| Failure Type | Evidence Status | Description |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['failure_type']}` | `{row['evidence_status']}` | {row['description']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The taxonomy is a mechanism-analysis scaffold. It is not a full-scale mechanism conclusion.",
        ]
    )
    write_text(report_path, "\n".join(lines) + "\n")
    manifest = create_mechanism_manifest(
        config=config,
        root=root,
        diagnostic_table_path=table_path,
        diagnostic_report_path=report_path,
        figure_paths=[],
        extra_output_paths=[json_path],
        evidence_sufficiency=str(evidence["evidence_sufficiency"]),
        insufficient_evidence=True,
        completed=True,
        notes="Failure taxonomy smoke artifact with negative-result preservation.",
    )
    write_manifest(output_dir / "mechanism_manifest.json", manifest)
    return MechanismAnalysisResult(
        config.analysis_name,
        config.analysis_type,
        config.scope,
        config.dataset_name,
        config.methods,
        summary,
        rows,
        str(evidence["evidence_sufficiency"]),
        {},
        {"table": table_path.as_posix(), "report": report_path.as_posix(), "json": json_path.as_posix()},
        config.smoke_only,
        config.protocol_only,
        True,
        False,
        "Failure taxonomy implemented; negative results preserved.",
    )

