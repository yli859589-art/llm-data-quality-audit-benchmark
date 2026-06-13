from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root
from filters_v2.validation import FilterManifestError, validate_filter_manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 4 filter manifests.")
    parser.add_argument("--path", default="artifacts/filter_outputs_step4")
    parser.add_argument("--include-step4", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    manifests = sorted(base.glob("**/filter_manifest.json")) if base.exists() else []
    errors: list[str] = []
    for path in manifests:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            validate_filter_manifest(manifest, root)
        except (json.JSONDecodeError, FilterManifestError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = path.as_posix()
            errors.append(f"{label}: {exc}")
    if args.include_step4 and not manifests:
        errors.append("No Step 4 filter manifests found.")
    report = {
        "status": "failed" if errors else "passed",
        "checked_manifests": len(manifests),
        "include_step4": bool(args.include_step4),
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "filter_manifest_check_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Filter manifest check failed.\n" + "\n".join(errors))
    print(f"Filter manifest check: ok ({len(manifests)} manifests)")


if __name__ == "__main__":
    main()
