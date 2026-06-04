from __future__ import annotations

import argparse

from experiment_utils import load_json_yaml, root

from data.real_corpora import load_documents_from_config
from scoring.hdqs_freeze import build_frozen_protocol


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    parser.add_argument("--dry-run-or-smoke", action="store_true")
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    dataset_config = config.get("dataset_config") or config["dataset_configs"][0]
    if not args.dry_run_or_smoke and config.get("mode") in {"paper", "full"}:
        raise SystemExit("Paper/full freezing must be run only after data preparation audit.")
    loaded = load_documents_from_config(root / dataset_config, root=root)
    output = root / "artifacts" / "frozen" / f"hdqspp_frozen_{loaded.dataset_key}.json"
    protocol = build_frozen_protocol(
        dataset_key=loaded.dataset_key,
        documents=loaded.documents,
        seed=int(loaded.metadata.get("seed", 13)),
        output_path=output,
    )
    print(f"Frozen protocol: {output}")
    print(f"Config SHA-256: {protocol['config_sha256']}")
    print(f"No test leakage: {protocol['no_test_leakage']}")


if __name__ == "__main__":
    main()
