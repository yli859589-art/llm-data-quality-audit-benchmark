from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from analysis_v2.validation import (
    MechanismManifestError,
    assert_mechanism_outputs_not_in_main_results,
    validate_mechanism_manifest,
)
from experiment_utils import root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 8 mechanism-analysis manifests.")
    parser.add_argument("--path", default="artifacts/analysis_step8")
    parser.add_argument("--include-step8", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    if base.is_file():
        manifests = [base] if base.name == "mechanism_manifest.json" else []
    else:
        manifests = sorted(base.glob("**/mechanism_manifest.json")) if base.exists() else []
    errors: list[str] = []
    for path in manifests:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            validate_mechanism_manifest(manifest, root)
        except (json.JSONDecodeError, MechanismManifestError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = path.as_posix()
            errors.append(f"{label}: {exc}")
    if args.include_step8 and not manifests:
        errors.append("No Step 8 mechanism manifests found.")
    try:
        assert_mechanism_outputs_not_in_main_results(root)
    except MechanismManifestError as exc:
        errors.append(str(exc))
    report = {
        "status": "failed" if errors else "passed",
        "checked_manifests": len(manifests),
        "include_step8": bool(args.include_step8),
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "mechanism_manifest_check_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Mechanism manifest check failed.\n" + "\n".join(errors))
    print(f"Mechanism manifest check: ok ({len(manifests)} manifests)")


if __name__ == "__main__":
    main()
