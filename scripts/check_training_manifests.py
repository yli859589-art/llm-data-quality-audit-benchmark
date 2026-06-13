from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root
from training_v2.validation import (
    TrainingManifestError,
    assert_training_outputs_not_in_main_results,
    validate_training_manifest,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 5 training manifests.")
    parser.add_argument("--path", default="artifacts/training_step5")
    parser.add_argument("--include-step5", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    manifests = sorted(base.glob("**/training_manifest.json")) if base.exists() else []
    errors: list[str] = []
    for path in manifests:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            validate_training_manifest(manifest, root)
        except (json.JSONDecodeError, TrainingManifestError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = path.as_posix()
            errors.append(f"{label}: {exc}")
    if args.include_step5 and not manifests:
        errors.append("No Step 5 training manifests found.")
    try:
        assert_training_outputs_not_in_main_results(root)
    except TrainingManifestError as exc:
        errors.append(str(exc))
    report = {
        "status": "failed" if errors else "passed",
        "checked_manifests": len(manifests),
        "include_step5": bool(args.include_step5),
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "training_manifest_check_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Training manifest check failed.\n" + "\n".join(errors))
    print(f"Training manifest check: ok ({len(manifests)} manifests)")


if __name__ == "__main__":
    main()
