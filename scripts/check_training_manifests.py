from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root

from artifacts_v2.legacy_integrity import legacy_exception
from training_v2.validation import (
    TrainingManifestError,
    assert_training_outputs_not_in_main_results,
    validate_training_manifest,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 5 training manifests.")
    parser.add_argument("--path", default="artifacts/training_step5")
    parser.add_argument("--include-step5", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    manifests = sorted(base.glob("**/training_manifest.json")) if base.exists() else []
    errors: list[str] = []
    exceptions: list[dict[str, str]] = []
    for path in manifests:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            validate_training_manifest(manifest, root)
        except (json.JSONDecodeError, TrainingManifestError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = path.as_posix()
            exception = legacy_exception(path, root)
            if exception:
                exceptions.append({"path": label, "error": str(exc), **exception})
            else:
                errors.append(f"{label}: {exc}")
    if args.include_step5 and not manifests:
        errors.append("No Step 5 training manifests found.")
    try:
        assert_training_outputs_not_in_main_results(root)
    except TrainingManifestError as exc:
        errors.append(str(exc))
    report = {
        "status": (
            "failed"
            if errors
            else ("passed_with_legacy_integrity_exceptions" if exceptions else "passed")
        ),
        "checked_manifests": len(manifests),
        "include_step5": bool(args.include_step5),
        "errors": errors,
        "legacy_integrity_exceptions": exceptions,
    }
    output = (
        args.output
        or root
        / "artifacts"
        / "upgrade_reports"
        / "manifest_checks"
        / "training_manifest_check_report.json"
    )
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Training manifest check failed.\n" + "\n".join(errors))
    print(
        "Training manifest check: ok "
        f"({len(manifests)} manifests; legacy exceptions={len(exceptions)})"
    )


if __name__ == "__main__":
    main()
