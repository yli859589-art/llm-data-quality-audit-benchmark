from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root

from analysis_v2.validation import (
    MechanismManifestError,
    assert_mechanism_outputs_not_in_main_results,
    validate_mechanism_manifest,
)
from artifacts_v2.legacy_integrity import legacy_exception


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 8 mechanism-analysis manifests.")
    parser.add_argument("--path", default="artifacts/analysis_step8")
    parser.add_argument("--include-step8", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    if base.is_file():
        manifests = [base] if base.name == "mechanism_manifest.json" else []
    else:
        manifests = sorted(base.glob("**/mechanism_manifest.json")) if base.exists() else []
    errors: list[str] = []
    exceptions: list[dict[str, str]] = []
    for path in manifests:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            validate_mechanism_manifest(manifest, root)
        except (json.JSONDecodeError, MechanismManifestError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = path.as_posix()
            exception = legacy_exception(path, root)
            if exception:
                exceptions.append({"path": label, "error": str(exc), **exception})
            else:
                errors.append(f"{label}: {exc}")
    if args.include_step8 and not manifests:
        errors.append("No Step 8 mechanism manifests found.")
    try:
        assert_mechanism_outputs_not_in_main_results(root)
    except MechanismManifestError as exc:
        errors.append(str(exc))
    report = {
        "status": (
            "failed"
            if errors
            else ("passed_with_legacy_integrity_exceptions" if exceptions else "passed")
        ),
        "checked_manifests": len(manifests),
        "include_step8": bool(args.include_step8),
        "errors": errors,
        "legacy_integrity_exceptions": exceptions,
    }
    output = (
        args.output
        or root
        / "artifacts"
        / "upgrade_reports"
        / "manifest_checks"
        / "mechanism_manifest_check_report.json"
    )
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Mechanism manifest check failed.\n" + "\n".join(errors))
    print(
        "Mechanism manifest check: ok "
        f"({len(manifests)} manifests; legacy exceptions={len(exceptions)})"
    )


if __name__ == "__main__":
    main()
