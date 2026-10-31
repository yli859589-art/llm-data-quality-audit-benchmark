#!/usr/bin/env python3
"""Non-destructive P0-1 environment, metadata, and real-corpus preflight.

Metadata mode permits a source-only checkout and explicitly reports absent
shards.  Full mode is a training gate: absent or hash-invalid real shards,
synthetic fallbacks, missing dependencies, and insufficient storage fail it.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATASETS = ("c4_en_v2_100m", "openwebtext_v2_100m")
PROTECTED_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".txt", ".svg"}
SYNTHETIC_MARKERS = ("synthetic", "mock", "fixture")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def paths(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else ([str(value)] if value else [])


def check(items: list[dict[str, str]], ident: str, status: str, detail: str, fix: str = "") -> None:
    items.append({"id": ident, "status": status, "detail": detail, "recommendation": fix})


def protected_snapshot(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for base in (root / "artifacts", root / "data"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and "upgrade_reports" not in path.parts and path.suffix.lower() in PROTECTED_SUFFIXES:
                result[path.relative_to(root).as_posix()] = sha256(path)
    return dict(sorted(result.items()))


def baseline_check(root: Path, baseline: Path | None, write: bool, items: list[dict[str, str]]) -> None:
    if write:
        if baseline is None:
            raise ValueError("--write-baseline requires --baseline-manifest")
        payload = {"schema_version": 1, "created_at": now(), "purpose": "P0-1 immutable historical artifact snapshot", "files": protected_snapshot(root)}
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        check(items, "baseline_snapshot", "pass", f"Wrote SHA-256 hashes for {len(payload['files'])} protected files.")
        return
    if baseline is None:
        check(items, "baseline_snapshot", "not_verified", "No baseline manifest supplied.", "Create one with --write-baseline before changing historical artifacts.")
        return
    if not baseline.exists():
        check(items, "baseline_snapshot", "fail", "Requested baseline manifest is absent.", "Create it with --write-baseline before continuing.")
        return
    expected = load_json(baseline).get("files", {})
    if not isinstance(expected, dict):
        check(items, "baseline_snapshot", "fail", "Baseline has no valid file-hash mapping.")
        return
    changed = [rel for rel, digest in expected.items() if not (root / rel).is_file() or sha256(root / rel) != str(digest).upper()]
    check(items, "baseline_snapshot", "pass" if not changed else "fail", f"Verified {len(expected)} protected files; changed or missing: {len(changed)}." + (f" Examples: {', '.join(changed[:3])}." if changed else ""), "Restore modified historical files or write new outputs outside protected locations." if changed else "")


def expected_hashes(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    sidecar = manifest.get("data_hashes")
    path = root / str(sidecar) if isinstance(sidecar, str) else None
    if path is None or not path.is_file():
        return {}
    split_hashes = load_json(path).get("split_sha256", {})
    split_paths = manifest.get("split_paths", {})
    result: dict[str, str] = {}
    if not isinstance(split_hashes, dict):
        return result
    for split, value in split_hashes.items():
        if isinstance(value, str):
            declared = paths(split_paths.get(split) if isinstance(split_paths, dict) else None)
            if len(declared) == 1:
                result[declared[0]] = value.upper()
        elif isinstance(value, dict):
            result.update({str(key): str(digest).upper() for key, digest in value.items()})
    return result


def dataset_check(root: Path, dataset: str, mode: str, items: list[dict[str, str]]) -> None:
    label = f"dataset.{dataset}"
    manifest_path = root / "artifacts" / "localmax_v2_data" / dataset / "data_manifest.json"
    if not manifest_path.is_file():
        check(items, f"{label}.manifest", "fail", "Data manifest is missing.", "Restore metadata or reacquire from the declared source.")
        return
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        check(items, f"{label}.manifest", "fail", f"Invalid manifest: {type(exc).__name__}: {exc}")
        return
    required = ("dataset_id", "source", "source_version", "document_count", "actual_gpt2_tokens", "split_paths", "split_gpt2_tokens", "split_document_counts", "fallback_used")
    absent = [key for key in required if key not in manifest]
    valid_id = manifest.get("dataset_id") == dataset
    check(items, f"{label}.manifest", "pass" if valid_id and not absent else "fail", f"dataset_id={manifest.get('dataset_id')!r}; documents={manifest.get('document_count')}; GPT-2 tokens={manifest.get('actual_gpt2_tokens')}." if valid_id and not absent else f"Incorrect dataset ID or missing fields: {', '.join(absent)}.")
    declared_source = " ".join(str(manifest.get(key, "")) for key in ("source", "source_config", "dataset_name")).casefold()
    fake = bool(manifest.get("fallback_used")) or any(marker in declared_source for marker in SYNTHETIC_MARKERS)
    check(items, f"{label}.no_synthetic_fallback", "fail" if fake else "pass", "Manifest declares synthetic/mock/fixture data or a fallback." if fake else "Manifest declares a non-synthetic source and fallback_used=false.", "Formal runs must restore the declared real corpus." if fake else "")
    token_counts, doc_counts = manifest.get("split_gpt2_tokens"), manifest.get("split_document_counts")
    try:
        totals_match = sum(int(value) for value in token_counts.values()) == int(manifest["actual_gpt2_tokens"]) and sum(int(value) for value in doc_counts.values()) == int(manifest["document_count"])
    except (AttributeError, TypeError, ValueError, KeyError):
        totals_match = False
    check(items, f"{label}.manifest_totals", "pass" if totals_match else "fail", "Split document/token totals agree with manifest totals." if totals_match else "Split totals do not agree with the manifest.")
    split_paths = manifest.get("split_paths", {})
    shard_paths = [rel for split in ("train", "valid", "test") for rel in paths(split_paths.get(split) if isinstance(split_paths, dict) else None)]
    missing = [rel for rel in shard_paths if not (root / rel).is_file()]
    missing_status = "pass" if not missing else ("warn" if mode == "metadata" else "fail")
    check(items, f"{label}.shards", missing_status, f"Referenced shards present: {len(shard_paths) - len(missing)}/{len(shard_paths)}." + (f" Missing: {', '.join(missing)}." if missing else ""), "Restore exact declared shards before full filtering/training." if missing else "")
    expected = expected_hashes(root, manifest)
    mismatch, unverified = [], []
    for rel in shard_paths:
        path = root / rel
        if not path.exists():
            continue
        if rel not in expected:
            unverified.append(rel)
        elif sha256(path) != expected[rel]:
            mismatch.append(rel)
    hash_status = "fail" if mismatch else ("pass" if not missing and not unverified else ("warn" if mode == "metadata" else "fail"))
    check(items, f"{label}.shard_hashes", hash_status, f"Verified {len(shard_paths)-len(missing)-len(unverified)-len(mismatch)} hashes; mismatches={len(mismatch)}, unverified={len(unverified)}.", "Restore the shard and validate it against data_hashes.json." if hash_status != "pass" else "")


def report(root: Path, mode: str, baseline: Path | None, write_baseline: bool) -> dict[str, Any]:
    items: list[dict[str, str]] = []
    required = ("src", "scripts", "configs", "tests", "artifacts", "data", "pyproject.toml", "requirements.txt", "requirements-dev.txt")
    missing = [name for name in required if not (root / name).exists()]
    check(items, "repository_layout", "pass" if not missing else "fail", "All required top-level paths are present." if not missing else f"Missing: {', '.join(missing)}.")
    baseline_check(root, baseline, write_baseline, items)
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8") if (root / "pyproject.toml").is_file() else ""
    check(items, "python_version", "pass" if sys.version_info >= (3, 10) and ">=3.10" in pyproject else "fail", f"Python {platform.python_version()}; project requires >=3.10.")
    packages = ("numpy", "torch", "datasets", "transformers", "yaml")
    absent_packages = [package for package in packages if importlib.util.find_spec(package) is None]
    check(items, "runtime_dependencies", "pass" if not absent_packages else "fail", "Required preflight packages are importable." if not absent_packages else f"Missing packages: {', '.join(absent_packages)}.", "Install requirements.txt (and data/tokenizer extras)." if absent_packages else "")
    try:
        import torch  # type: ignore

        check(items, "device_selection", "pass", f"torch {torch.__version__}; CUDA available={torch.cuda.is_available()}. CPU is supported when CUDA is unavailable.")
    except Exception as exc:
        check(items, "device_selection", "fail", f"torch import failed: {type(exc).__name__}: {exc}")
    for dataset in DATASETS:
        dataset_check(root, dataset, mode, items)
    free_gb = shutil.disk_usage(root).free / 1024**3
    disk_status = "pass" if free_gb >= 25 else ("warn" if mode == "metadata" else "fail")
    check(items, "disk_reserve", disk_status, f"Free space: {free_gb:.2f} GiB; LocalMax data preparation reserves 25 GiB.", "Free disk capacity before a full run." if disk_status != "pass" else "")
    failed = [entry["id"] for entry in items if entry["status"] == "fail"]
    warned = [entry["id"] for entry in items if entry["status"] in {"warn", "not_verified"}]
    return {"schema_version": 1, "tool": "scripts/preflight_project.py", "created_at": now(), "mode": mode, "repository_root": ".", "overall_status": "fail" if failed else "pass", "exit_code": 1 if failed else 0, "summary": {"checks": len(items), "failures": len(failed), "warnings_or_unverified": len(warned)}, "failures": failed, "warnings_or_unverified": warned, "checks": items}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mode", choices=("metadata", "full"), default="metadata")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline-manifest", type=Path)
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "artifacts" / "upgrade_reports" / "p0-01_preflight" / f"preflight_{args.mode}.json"
    output = output if output.is_absolute() else root / output
    baseline = args.baseline_manifest
    baseline = (baseline if baseline is None or baseline.is_absolute() else root / baseline)
    try:
        payload = report(root, args.mode, baseline, args.write_baseline)
    except Exception as exc:
        payload = {"schema_version": 1, "tool": "scripts/preflight_project.py", "created_at": now(), "mode": args.mode, "overall_status": "fail", "exit_code": 1, "summary": {"checks": 1, "failures": 1, "warnings_or_unverified": 0}, "failures": ["preflight_internal_error"], "warnings_or_unverified": [], "checks": [{"id": "preflight_internal_error", "status": "fail", "detail": f"{type(exc).__name__}: {exc}", "recommendation": "Fix the invalid input or report a checker defect."}]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Preflight {payload['overall_status']}: {len(payload['checks'])} checks; report={output}")
    for entry in payload["checks"]:
        print(f"[{entry['status'].upper()}] {entry['id']}: {entry['detail']}")
    return int(payload["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
