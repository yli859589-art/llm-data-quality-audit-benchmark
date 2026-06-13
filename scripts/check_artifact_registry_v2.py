from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from artifacts_v2.registry import read_registry
from artifacts_v2.validation import validate_registry_rows
from experiment_utils import root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate artifact registry v2.")
    parser.add_argument("--path", default="artifacts/registry_v2/artifact_registry.jsonl")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    registry_path = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    if not registry_path.exists():
        raise SystemExit(f"Missing artifact registry v2: {registry_path}")
    rows = read_registry(registry_path)
    errors = validate_registry_rows(rows, root)
    report = {
        "status": "failed" if errors else "passed",
        "record_count": len(rows),
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "artifact_registry_v2_validation_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Artifact registry v2 check failed.\n" + "\n".join(errors))
    print(f"Artifact registry v2 check: ok ({len(rows)} records)")


if __name__ == "__main__":
    main()

