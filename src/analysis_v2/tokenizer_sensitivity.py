from __future__ import annotations

from pathlib import Path

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, write_manifest
from .reporting import mechanism_report


def run_tokenizer_sensitivity_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    bpe_smoke = root / "artifacts" / "tokenizers_step3" / "bpe_smoke" / "tokenizer_manifest.json"
    char_manifest = root / "artifacts" / "tokenizers_step3" / "char" / "tokenizer_manifest.json"
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=0,
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["char/BPE matched tokenizer matrix", "BPE16k/BPE32k manifests", "selection-overlap audit"],
    )
    row = {
        "method_name": config.methods[0] if config.methods else "protocol_only",
        "char_manifest_status": "available" if char_manifest.exists() else "unavailable",
        "lightweight_bpe_smoke_status": "available" if bpe_smoke.exists() else "unavailable",
        "formal_bpe16k_status": "future_required",
        "formal_bpe32k_status": "future_required",
        "token_budget_mismatch_warning": "future_matrix_required",
        "selection_overlap_available": False,
        "tokenizer_sensitivity_completed": False,
        "insufficient_evidence": True,
        "notes": "Protocol-only tokenizer sensitivity plan; smoke tokenizer is not a formal tokenizer matrix.",
    }
    summary = {
        "bpe_smoke_manifest_available": bpe_smoke.exists(),
        "char_manifest_available": char_manifest.exists(),
        "formal_tokenizer_matrix_completed": False,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "tokenizer_sensitivity_diagnostics.csv"
    summary_path = output_dir / "tokenizer_sensitivity_summary.json"
    report_path = output_dir / "tokenizer_sensitivity_report.md"
    write_csv(table_path, [row])
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Tokenizer Sensitivity Protocol",
            summary,
            "The current artifact is protocol-only and distinguishes smoke tokenization from future formal BPE matrices.",
        ),
    )
    manifest = create_mechanism_manifest(
        config=config,
        root=root,
        diagnostic_table_path=table_path,
        diagnostic_report_path=report_path,
        figure_paths=[],
        extra_output_paths=[summary_path],
        evidence_sufficiency=str(evidence["evidence_sufficiency"]),
        insufficient_evidence=True,
        completed=False,
        notes="Tokenizer sensitivity protocol only.",
    )
    write_manifest(output_dir / "mechanism_manifest.json", manifest)
    return MechanismAnalysisResult(
        config.analysis_name,
        config.analysis_type,
        config.scope,
        config.dataset_name,
        config.methods,
        summary,
        [row],
        str(evidence["evidence_sufficiency"]),
        {},
        {"table": table_path.as_posix(), "report": report_path.as_posix(), "summary": summary_path.as_posix()},
        config.smoke_only,
        config.protocol_only,
        True,
        False,
        "Protocol-only tokenizer-sensitivity plan.",
    )

