from __future__ import annotations

MANIFEST_VERSION = "step8.mechanism_manifest.v1"

VALID_SCOPES = {
    "smoke",
    "sample",
    "main_protocol",
    "level2_protocol",
    "level3_heavy_protocol",
    "completed_run",
}

PROTOCOL_SCOPES = {"main_protocol", "level2_protocol", "level3_heavy_protocol"}

VALID_ANALYSIS_TYPES = {
    "proxy_utility",
    "overfiltering",
    "diversity_loss",
    "domain_shift",
    "rank_stability",
    "tokenizer_sensitivity",
    "scale_trend",
    "failure_taxonomy",
    "pareto_mechanism",
    "combined",
    "combined_smoke",
}

VALID_EVIDENCE_SUFFICIENCY = {
    "sufficient",
    "insufficient",
    "protocol_only",
    "smoke_diagnostic_only",
}

PROTECTED_RESULT_FILES = [
    "artifacts/tables/main_results.csv",
    "artifacts/stats/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
]

