"""Read-only registry for imported artifacts with pre-baseline hash defects.

The validators intentionally remain strict.  This registry is consulted only by
repository-wide checker commands so an imported, immutable defect is reported
as an exception rather than silently accepted as valid evidence.
"""

from __future__ import annotations

from pathlib import Path

LEGACY_INTEGRITY_EXCEPTIONS: dict[str, dict[str, str]] = {
    "artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json": {
        "reason": "dataset_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/filter_outputs_step6/wikitext2_smoke/urd_ablation_no_risk/filter_manifest.json": {
        "reason": "dataset_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/filter_manifest.json": {
        "reason": "dataset_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/filter_outputs_step6/wikitext2_smoke/urd_pareto/filter_manifest.json": {
        "reason": "dataset_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/failure_taxonomy/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/rank_stability_protocol/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/scale_trend_protocol/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/tokenizer_sensitivity_protocol/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/wikitext2_smoke/diversity_loss_urd_fixed/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/wikitext2_smoke/domain_shift_urd_fixed/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/wikitext2_smoke/overfiltering_urd_fixed/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    (
        "artifacts/analysis_step8/wikitext2_smoke/pareto_mechanism_urd_pareto/"
        "mechanism_manifest.json"
    ): {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/analysis_step8/wikitext2_smoke/proxy_utility_urd_fixed/mechanism_manifest.json": {
        "reason": "diagnostic_table_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and generate new versioned output.",
    },
    "artifacts/evaluation_step7/downstream_protocol/evaluation_manifest.json": {
        "reason": (
            "metrics_hash and report_hash predate the imported baseline and do not match "
            "preserved files"
        ),
        "remediation": "Use the read-only integrity audit; do not rewrite evidence.",
    },
    "artifacts/evaluation_step7/stability_protocol/evaluation_manifest.json": {
        "reason": "metrics_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and record a read-only integrity exception.",
    },
    "artifacts/evaluation_step7/wikitext2_smoke/cost_urd_fixed/evaluation_manifest.json": {
        "reason": "filter_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and record a read-only integrity exception.",
    },
    "artifacts/evaluation_step7/wikitext2_smoke/diversity_urd_fixed/evaluation_manifest.json": {
        "reason": "filter_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and record a read-only integrity exception.",
    },
    "artifacts/evaluation_step7/wikitext2_smoke/lm_bpe_tiny/evaluation_manifest.json": {
        "reason": "training_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and record a read-only integrity exception.",
    },
    "artifacts/evaluation_step7/wikitext2_smoke/pareto_urd_pareto/evaluation_manifest.json": {
        "reason": "filter_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and record a read-only integrity exception.",
    },
    "artifacts/evaluation_step7/wikitext2_smoke/risk_urd_fixed/evaluation_manifest.json": {
        "reason": "filter_manifest_hash is a preserved pre-baseline mismatch",
        "remediation": "Preserve legacy evidence and record a read-only integrity exception.",
    },
}


def legacy_exception(path: Path, root: Path) -> dict[str, str] | None:
    """Return the documented exception for an immutable imported artifact."""
    try:
        return LEGACY_INTEGRITY_EXCEPTIONS.get(
            path.resolve().relative_to(root.resolve()).as_posix()
        )
    except ValueError:
        return None
