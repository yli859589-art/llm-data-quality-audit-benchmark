from __future__ import annotations

MANIFEST_VERSION = "step7.evaluation_manifest.v1"

VALID_SCOPES = {
    "smoke",
    "sample",
    "main_protocol",
    "level2_protocol",
    "level3_heavy_protocol",
    "completed_run",
}

VALID_EVALUATION_TYPES = {
    "lm",
    "downstream",
    "downstream_protocol",
    "risk",
    "diversity",
    "cost",
    "stability",
    "pareto",
    "combined",
    "combined_smoke",
}

PROTOCOL_SCOPES = {"main_protocol", "level2_protocol", "level3_heavy_protocol"}

PROTECTED_RESULT_FILES = [
    "artifacts/tables/main_results.csv",
    "artifacts/stats/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
]
