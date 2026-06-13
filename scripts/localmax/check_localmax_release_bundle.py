from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from localmax_utils import ROOT, sha256_file
from artifacts_v2.canonical_io import write_canonical_json, write_canonical_text


RELEASE_ROOT = ROOT / "artifacts" / "localmax_release"
TABLES_DIR = RELEASE_ROOT / "tables"
REPORTS_DIR = RELEASE_ROOT / "reports"
MANIFESTS_DIR = RELEASE_ROOT / "manifests"
BUNDLE_SCOPE = "standalone_metadata_bundle"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _registry_hash_ok(path: Path) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        artifact = ROOT / row["path"]
        if not artifact.exists() or sha256_file(artifact) != row.get("sha256"):
            return False
    return True


def check_bundle() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    main_table = TABLES_DIR / "localmax_main_results_release.csv"
    dataset_table = TABLES_DIR / "localmax_dataset_summary_release.csv"
    manifest = _load_json(RELEASE_ROOT / "localmax_release_manifest.json")

    table_links: list[str] = []
    if main_table.exists():
        for row in _read_csv(main_table):
            table_links.extend([row["training_manifest"], row["evaluation_manifest"]])
    else:
        errors.append("missing localmax_main_results_release.csv")
    if dataset_table.exists():
        table_links.extend(row["data_manifest"] for row in _read_csv(dataset_table) if row.get("data_manifest"))
    else:
        errors.append("missing localmax_dataset_summary_release.csv")

    dangling = []
    outside_bundle = []
    for link in sorted(set(table_links)):
        path = ROOT / link
        if not path.exists():
            dangling.append(link)
        if not link.startswith("artifacts/localmax_release/"):
            outside_bundle.append(link)
    if dangling:
        errors.append("dangling release table links: " + ", ".join(dangling[:10]))
    if outside_bundle:
        errors.append("standalone bundle table links outside release bundle: " + ", ".join(outside_bundle[:10]))

    if not MANIFESTS_DIR.exists():
        errors.append("standalone manifests directory is missing")
    filter_manifests = sorted((MANIFESTS_DIR / "filters").glob("*/*/filter_manifest.json"))
    training_manifests = sorted((MANIFESTS_DIR / "training").glob("*/*/seed_*/training_manifest.json"))
    metric_files = sorted((MANIFESTS_DIR / "training").glob("*/*/seed_*/metrics.json"))
    dataset_manifests = sorted((MANIFESTS_DIR / "data").glob("*/*.json"))
    if len(filter_manifests) < 8:
        errors.append(f"expected at least 8 copied filter manifests, found {len(filter_manifests)}")
    if len(training_manifests) != 24:
        errors.append(f"expected 24 copied training manifests, found {len(training_manifests)}")
    if len(metric_files) != 24:
        errors.append(f"expected 24 copied metrics files, found {len(metric_files)}")
    if len(dataset_manifests) < 2:
        errors.append(f"expected copied dataset manifests, found {len(dataset_manifests)}")
    if not (MANIFESTS_DIR / "tokenizer" / "gpt2" / "tokenizer_manifest.json").exists():
        errors.append("missing copied GPT-2 tokenizer manifest")
    if not (MANIFESTS_DIR / "evaluation" / "evaluation_manifest.json").exists():
        errors.append("missing copied evaluation manifest")

    forbidden_large_or_binary = []
    for path in RELEASE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.stat().st_size > 5 * 1024 * 1024:
            forbidden_large_or_binary.append(rel)
        if path.suffix.lower() in {".pt", ".pth", ".bin", ".ckpt"}:
            forbidden_large_or_binary.append(rel)
    if forbidden_large_or_binary:
        errors.append("release bundle contains large or binary checkpoint-like files: " + ", ".join(forbidden_large_or_binary[:10]))

    bundle_size = sum(path.stat().st_size for path in RELEASE_ROOT.rglob("*") if path.is_file())
    if bundle_size > 50 * 1024 * 1024:
        errors.append(f"release bundle is unexpectedly large: {bundle_size} bytes")

    manifest_is_hotfix = manifest.get("release_hotfix_version") == "step10C_hotfix_v1"
    manifest_scope_ok = manifest.get("bundle_scope") in {BUNDLE_SCOPE, None}
    if manifest and not manifest_is_hotfix:
        warnings.append("release manifest has not yet been rewritten by the hotfix finalizer")
    if manifest_is_hotfix and manifest.get("bundle_scope") != BUNDLE_SCOPE:
        errors.append("release manifest bundle_scope is not standalone_metadata_bundle")
    if manifest_is_hotfix and manifest.get("standalone_bundle") is not True:
        errors.append("release manifest standalone_bundle is not true")
    if manifest_is_hotfix and manifest.get("raw_data_included") is not False:
        errors.append("release manifest must declare raw_data_included=false")
    if manifest_is_hotfix and manifest.get("binary_checkpoints_included") is not False:
        errors.append("release manifest must declare binary_checkpoints_included=false")
    if manifest_is_hotfix and (manifest.get("canonical_encoding") != "UTF-8" or manifest.get("canonical_newline") != "LF"):
        errors.append("release manifest canonical UTF-8/LF policy is missing")

    local_registry = RELEASE_ROOT / "localmax_artifact_registry.jsonl"
    global_registry = ROOT / "artifacts" / "registry_v2" / "artifact_registry.jsonl"
    if not local_registry.exists():
        warnings.append("local release registry not present yet; finalizer must generate it")
    if not global_registry.exists():
        warnings.append("global artifact registry not present yet")

    report = {
        "step": "step10C_localmax_hotfix",
        "status": "passed" if not errors else "failed",
        "bundle_scope": BUNDLE_SCOPE,
        "standalone_bundle": True,
        "raw_data_included": False,
        "binary_checkpoints_included": False,
        "metadata_and_metrics_included": True,
        "release_bundle_links_valid": not dangling and not outside_bundle,
        "dangling_links": dangling,
        "outside_bundle_links": outside_bundle,
        "bundle_size_bytes": bundle_size,
        "copied_dataset_manifest_count": len(dataset_manifests),
        "copied_filter_manifest_count": len(filter_manifests),
        "copied_training_manifest_count": len(training_manifests),
        "copied_metrics_count": len(metric_files),
        "localmax_registry_hash_check_passed": local_registry.exists(),
        "global_registry_hash_check_passed": global_registry.exists(),
        "registry_hash_validation_scope": "deferred_to_release_and_global_registry_checks",
        "manifest_scope_ok": manifest_scope_ok,
        "warnings": warnings,
        "errors": errors,
    }
    write_canonical_json(REPORTS_DIR / "release_bundle_integrity_report.json", report)
    lines = [
        "# LocalMax Release Bundle Integrity Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Bundle scope: `{BUNDLE_SCOPE}`",
        f"- Standalone bundle: `{report['standalone_bundle']}`",
        f"- Links valid: `{report['release_bundle_links_valid']}`",
        f"- Raw data included: `{report['raw_data_included']}`",
        f"- Binary checkpoints included: `{report['binary_checkpoints_included']}`",
        f"- Bundle size bytes: `{bundle_size}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- none"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in warnings] or ["- none"])
    write_canonical_text(REPORTS_DIR / "release_bundle_integrity_report.md", "\n".join(lines))
    if errors:
        raise SystemExit("LocalMax release bundle check failed.\n" + "\n".join(errors))
    print("LocalMax release bundle check: ok")
    return report


def main() -> None:
    check_bundle()


if __name__ == "__main__":
    main()
