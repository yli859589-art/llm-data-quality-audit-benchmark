from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path
from typing import Any

from data_sources.manifest import MANIFEST_VERSION
from data_sources.validation import DatasetManifestError, validate_manifest
from experiment_utils import root


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scan_paths(include_step2: bool) -> list[Path]:
    paths = sorted((root / "artifacts" / "data").glob("**/data_manifest.json"))
    step2_root = root / "artifacts" / "data_step2"
    if include_step2 or step2_root.exists():
        paths.extend(sorted(step2_root.glob("**/data_manifest.json")))
    unique: list[Path] = []
    seen = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return unique


def _validate_legacy_manifest(path: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    dataset_scope = str(manifest.get("dataset_scope", ""))
    dataset_status = str(manifest.get("dataset_status", ""))
    allow_fallback = bool(manifest.get("allow_fallback", False))
    used_fallback = bool(manifest.get("used_fallback", False))
    if dataset_scope in {"official_split", "streaming_sample"} and used_fallback:
        errors.append(f"{path.relative_to(root)} has used_fallback=true in {dataset_scope}")
    if dataset_scope in {"official_split", "streaming_sample"} and dataset_status in {"real_nonfallback", "real_local_nonfallback"}:
        if allow_fallback:
            errors.append(f"{path.relative_to(root)} allows fallback despite real non-fallback scope")
    if manifest.get("is_full_dataset") is True and dataset_scope == "streaming_sample":
        errors.append(f"{path.relative_to(root)} marks streaming_sample as full dataset")
    if "smoke" in str(manifest.get("dataset_key", "")).casefold() and dataset_scope in {"main", "heavy"}:
        errors.append(f"{path.relative_to(root)} appears to promote smoke data to main/heavy")
    return errors


def _validate_step2_manifest(path: Path, manifest: dict[str, Any]) -> list[str]:
    try:
        validate_manifest(manifest, root)
    except DatasetManifestError as exc:
        return [f"{path.relative_to(root)}: {exc}"]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate legacy and Step 2 dataset manifests.")
    parser.add_argument("--include-step2", action="store_true")
    args = parser.parse_args()

    paths = _scan_paths(args.include_step2)
    errors: list[str] = []
    step2_count = 0
    legacy_count = 0
    for path in paths:
        manifest = _load_json(path)
        if manifest.get("manifest_version") == MANIFEST_VERSION:
            step2_count += 1
            errors.extend(_validate_step2_manifest(path, manifest))
        else:
            legacy_count += 1
            errors.extend(_validate_legacy_manifest(path, manifest))

    report = {
        "status": "failed" if errors else "passed",
        "checked_manifests": len(paths),
        "legacy_manifests": legacy_count,
        "step2_manifests": step2_count,
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "dataset_manifest_check_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Dataset manifest check failed.\n" + "\n".join(errors))
    print(
        "Dataset manifest check: ok "
        f"({len(paths)} manifests; legacy={legacy_count}; step2={step2_count})"
    )


if __name__ == "__main__":
    main()
