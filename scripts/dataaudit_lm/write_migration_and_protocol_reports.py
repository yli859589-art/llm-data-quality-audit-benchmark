from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.hashing import sha256_file, sha256_json
from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.integrity.paths import INTEGRITY, REPORTS


MIGRATION_ROWS = [
    ("data_loading", "legacy local-scale scripts", "src/dataaudit_lm/data", "VALIDATED"),
    ("tokenizer", "src/tokenization", "future src/dataaudit_lm/tokenization", "ADAPTER_ONLY"),
    (
        "dataset_manifest",
        "src/data_sources/manifest.py",
        "src/dataaudit_lm/data/manifests.py",
        "MIGRATED",
    ),
    ("filtering_methods", "src/filters_v2", "src/dataaudit_lm/filters", "VALIDATED"),
    ("model_definition", "src/models_v2", "src/dataaudit_lm/models", "MIGRATED"),
    ("training_loop", "src/training_v2", "src/dataaudit_lm/training", "MIGRATED"),
    (
        "checkpoint",
        "legacy local-scale artifacts",
        "src/dataaudit_lm/training/checkpoints.py",
        "MIGRATED",
    ),
    (
        "lm_evaluation",
        "src/evaluation_v2/lm_metrics.py",
        "src/dataaudit_lm/evaluation/lm_metrics.py",
        "VALIDATED",
    ),
    (
        "downstream",
        "src/evaluation_v2/downstream.py",
        "src/dataaudit_lm/evaluation/downstream.py",
        "MIGRATED",
    ),
    ("statistics", "src/evaluation_v2/statistics.py", "src/dataaudit_lm/statistics", "MIGRATED"),
    ("registry", "artifacts_v2", "src/dataaudit_lm/registry", "ADAPTER_ONLY"),
    ("hash_integrity", "mixed scripts", "src/dataaudit_lm/integrity", "VALIDATED"),
    (
        "figure_table_generation",
        "legacy figure scripts",
        "future src/dataaudit_lm/reporting",
        "NOT_STARTED",
    ),
    (
        "release_tooling",
        "legacy release scripts",
        "scripts/dataaudit_lm/finalize_release.py",
        "MIGRATED",
    ),
]


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    INTEGRITY.mkdir(parents=True, exist_ok=True)
    migration = {
        "migration_map_version": "dataaudit_lm_migration_map_v1",
        "allowed_statuses": [
            "NOT_STARTED",
            "ADAPTER_ONLY",
            "MIGRATED",
            "VALIDATED",
            "LEGACY_REMOVABLE",
        ],
        "rows": [
            {
                "module": module,
                "legacy_path": legacy,
                "canonical_new_path": new,
                "migration_status": status,
                "runtime_dependency": (
                    "new package"
                    if status in {"MIGRATED", "VALIDATED"}
                    else "legacy/artifact adapter"
                ),
                "artifact_dependency": "legacy evidence retained until frozen final matrix",
                "tests_covering_it": "tests/test_dataaudit_*.py",
                "planned_removal_stage": "after frozen protocol and parity audit",
            }
            for module, legacy, new, status in MIGRATION_ROWS
        ],
    }
    migration["migration_map_hash"] = sha256_json(migration)
    write_json(REPORTS / "migration_map.json", migration)

    protocol_path = ROOT / "configs/dataaudit_lm/frozen_protocol.yaml"
    statistical_path = ROOT / "configs/dataaudit_lm/statistical_analysis.yaml"
    freeze = {
        "protocol_freeze_version": "dataaudit_lm_rehearsal_freeze_v1",
        "status": "frozen_for_rehearsal_only",
        "formal_training_started": False,
        "protocol_path": protocol_path.relative_to(ROOT).as_posix(),
        "protocol_sha256": sha256_file(protocol_path),
        "statistical_protocol_path": statistical_path.relative_to(ROOT).as_posix(),
        "statistical_protocol_sha256": sha256_file(statistical_path),
        "planned_final_matrix": "2 datasets x 6-8 independent methods x at least 5 seeds",
    }
    freeze["freeze_manifest_hash"] = sha256_json(freeze)
    write_json(INTEGRITY / "protocol_freeze_manifest.json", freeze)
    print(json.dumps({"migration_rows": len(migration["rows"]), "freeze_status": freeze["status"]}))


if __name__ == "__main__":
    main()
