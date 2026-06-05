from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import hashlib
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from experiment_utils import root


PROTECTED_HASHES = {
    "artifacts/tables/main_results.csv": "eab3478d19e04caf97e07fc31fcd3cc36089c19320a64e96f7bac9eb12d89921",
    "artifacts/cross_dataset/cross_dataset_results.csv": "8da3e015146193fcd5d1f5f47a9e0a5ed84f55a4182b4bb5932dc657b8daad4c",
    "artifacts/runs/run_registry.jsonl": "a05a06fca305cedf2c46dbead17ac222a5f09e73ab105538479a049df90a26ce",
    "artifacts/stats/main_results.csv": "e40944bb6476d84e8c3fc65670b2dc5e7db62cf47ca7fc6d0051768458cd0e32",
    "artifacts/experiment_readiness_report.json": "9456f46adc79f21026439a5b6504f14c3029022afe977f3ca066d6c2c513f1e1",
}

ZIP_REQUIRED_ENTRIES = {
    "README.md",
    "Makefile",
    "PROJECT_SUMMARY.md",
    "PROJECT_ONE_PAGE.md",
    "TECHNICAL_OVERVIEW.md",
    "DEMO_GUIDE.md",
    "RESUME_BULLETS.md",
    "docs/README.md",
    "docs/QUICKSTART.md",
    "docs/REPRODUCIBILITY.md",
    "docs/BENCHMARK_PROTOCOL.md",
    "docs/ARTIFACT_INDEX.md",
    "docs/PROJECT_PRESENTATION_NOTES.md",
    "docs/FIGURE_INDEX.md",
    "docs/future_publication_notes/README.md",
    "scripts/run_all_checks.py",
    "scripts/run_release_checks.py",
    "scripts/verify_fresh_unzip.py",
    "scripts/generate_final_release_report.py",
    "artifacts/tables/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
    "artifacts/cross_dataset/dataset_status_matrix.csv",
    "artifacts/release/claim_hygiene_report.json",
    "artifacts/release/claim_hygiene_report.md",
    "artifacts/release/fresh_unzip_report.json",
    "artifacts/release/fresh_unzip_report.md",
    "artifacts/release/final_release_report.json",
    "artifacts/release/final_release_report.md",
}

CACHE_PATTERN = re.compile(
    r"__pycache__|\.pyc$|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.coverage|\.ipynb_checkpoints"
)
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:(?<![A-Za-z])[A-Za-z]:(?:\\+|/(?!/))|/(?:home|Users|mnt/data|tmp)(?:/|$))"
)
TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".py", ".toml", ".cff"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize(text: str) -> str:
    text = re.sub(r"[A-Za-z]:[\\/]+Users[\\/]+[^'\"\r\n ]+", "<local_user_path>", text)
    text = re.sub(r"[A-Za-z]:[\\/]+[^'\"\r\n ]+", "<local_absolute_path>", text)
    text = re.sub(r"/(?:home|Users|mnt/data|tmp)/[^'\"\r\n ]+", "<local_absolute_path>", text)
    return text


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_validation(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Validation item must use name=status format: {item}")
        name, status = item.split("=", 1)
        parsed[name.strip()] = status.strip()
    return parsed


def _protected_hash_report() -> dict[str, dict[str, Any]]:
    report: dict[str, dict[str, Any]] = {}
    for relative, expected in PROTECTED_HASHES.items():
        path = root / relative
        actual = _sha256(path) if path.exists() else ""
        report[relative] = {
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches_expected": actual == expected,
        }
    return report


def _cross_dataset_status() -> list[dict[str, str]]:
    path = root / "artifacts/cross_dataset/dataset_status_matrix.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _zip_report(zip_path: Path | None) -> dict[str, Any]:
    if zip_path is None:
        return {
            "status": "not_run",
            "zip_file_name": "",
            "zip_path": "",
            "zip_sha256": "",
            "size_bytes": 0,
            "entry_count": 0,
            "required_missing": sorted(ZIP_REQUIRED_ENTRIES),
            "cache_hits": [],
            "nested_zip_hits": [],
            "absolute_path_hits": [],
        }
    zip_path = zip_path.resolve()
    if not zip_path.exists():
        return {
            "status": "failed",
            "zip_file_name": zip_path.name,
            "zip_path": _sanitize(str(zip_path)),
            "zip_sha256": "",
            "size_bytes": 0,
            "entry_count": 0,
            "required_missing": sorted(ZIP_REQUIRED_ENTRIES),
            "cache_hits": [],
            "nested_zip_hits": [],
            "absolute_path_hits": [],
            "error": "zip_not_found",
        }

    cache_hits: list[str] = []
    nested_zip_hits: list[str] = []
    absolute_path_hits: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = [name.replace("\\", "/") for name in archive.namelist()]
        name_set = set(names)
        for original_name, normalized in zip(archive.namelist(), names, strict=True):
            if CACHE_PATTERN.search(normalized):
                cache_hits.append(normalized)
            if normalized.lower().endswith(".zip"):
                nested_zip_hits.append(normalized)
            if Path(normalized).suffix.lower() not in TEXT_SUFFIXES and Path(normalized).name not in {".gitignore"}:
                continue
            try:
                text = archive.read(original_name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if ABSOLUTE_PATH_PATTERN.search(text):
                absolute_path_hits.append(normalized)
    required_missing = sorted(ZIP_REQUIRED_ENTRIES.difference(name_set))
    clean = not cache_hits and not nested_zip_hits and not absolute_path_hits and not required_missing
    return {
        "status": "passed" if clean else "failed",
        "zip_file_name": zip_path.name,
        "zip_path": _sanitize(str(zip_path)),
        "zip_sha256": _sha256(zip_path),
        "size_bytes": zip_path.stat().st_size,
        "entry_count": len(names),
        "required_missing": required_missing,
        "cache_hits": cache_hits,
        "nested_zip_hits": nested_zip_hits,
        "absolute_path_hits": absolute_path_hits,
    }


def build_report(zip_path: Path | None, validation: dict[str, str]) -> dict[str, Any]:
    readiness = _load_json(root / "artifacts/experiment_readiness_report.json")
    claim_hygiene = _load_json(root / "artifacts/release/claim_hygiene_report.json")
    fresh_unzip = _load_json(root / "artifacts/release/fresh_unzip_report.json")
    protected = _protected_hash_report()
    all_protected_match = all(item["matches_expected"] for item in protected.values())
    main_results_modified = not protected["artifacts/tables/main_results.csv"]["matches_expected"]
    zip_info = _zip_report(zip_path)
    report = {
        "status": "release_candidate",
        "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "readiness": readiness.get("readiness_level", ""),
        "method_status": readiness.get("method_status", ""),
        "benchmark_scope_status": readiness.get("benchmark_scope_status", ""),
        "secondary_method_finding": "hdqspp_v3_improves_over_v2_trend_but_not_raw",
        "ccf_c_ready": readiness.get("ccf_c_ready", ""),
        "main_results_modified": main_results_modified,
        "experiment_results_modified": not all_protected_match,
        "protected_result_files": protected,
        "claim_hygiene_status": claim_hygiene.get("status", "not_run"),
        "fresh_unzip": {
            "status": fresh_unzip.get("status", "not_run"),
            "lightweight_check_status": fresh_unzip.get("lightweight_check_status", "not_run"),
            "heavy_check_status": fresh_unzip.get("heavy_check_status", "not_run"),
            "heavy_check_reason": fresh_unzip.get("heavy_check_reason", ""),
            "cache_scan_status": fresh_unzip.get("cache_scan_status", ""),
            "nested_zip_scan_status": fresh_unzip.get("nested_zip_scan_status", ""),
            "local_absolute_path_scan_status": fresh_unzip.get("local_absolute_path_scan_status", ""),
        },
        "validation": validation,
        "zip": zip_info,
        "cross_dataset_status": _cross_dataset_status(),
        "release_boundary": [
            "Audit benchmark release candidate.",
            "HDQS++ v3 does not outperform raw under the current fair benchmark.",
            "OpenWebText/C4 evidence is streaming-sample evidence only.",
            "No new 4A experiments are included in this release.",
        ],
        "roadmap_4a_not_executed": [
            "BPE tokenizer",
            "medium model",
            "larger OpenWebText/C4 streaming samples",
            "stronger seed budget",
            "held-out test evaluation after freezing",
            "compute logs and larger-scale mechanism diagnostics",
        ],
    }
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    output_path = root / "artifacts/release/final_release_report.md"
    protected_rows = []
    for relative, item in report["protected_result_files"].items():
        protected_rows.append(
            f"| `{relative}` | `{item['matches_expected']}` | `{item['actual_sha256']}` |"
        )
    validation_rows = [
        f"| `{name}` | `{status}` |" for name, status in sorted(report["validation"].items())
    ]
    if not validation_rows:
        validation_rows = ["|  | `not_run` |"]
    zip_info = report["zip"]
    lines = [
        "# Final Release Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Version: `{report['version']}`",
        f"- readiness: `{report['readiness']}`",
        f"- method_status: `{report['method_status']}`",
        f"- benchmark_scope_status: `{report['benchmark_scope_status']}`",
        f"- secondary_method_finding: `{report['secondary_method_finding']}`",
        f"- ccf_c_ready: `{str(report['ccf_c_ready']).lower()}`",
        f"- main_results_modified: `{str(report['main_results_modified']).lower()}`",
        f"- experiment_results_modified: `{str(report['experiment_results_modified']).lower()}`",
        "",
        "## Fresh-Unzip Status",
        "",
        f"- fresh-unzip status: `{report['fresh_unzip']['status']}`",
        f"- fresh-unzip lightweight_check_status: `{report['fresh_unzip']['lightweight_check_status']}`",
        f"- fresh-unzip heavy_check_status: `{report['fresh_unzip']['heavy_check_status']}`",
        f"- fresh-unzip heavy_check_reason: {report['fresh_unzip']['heavy_check_reason']}",
        "",
        "A skipped heavy check is reported as `skipped_by_request`, not as passed.",
        "",
        "## Validation Commands",
        "",
        "| Command group | Status |",
        "|---|---|",
        *validation_rows,
        "",
        "## Zip Cleanliness",
        "",
        f"- zip status: `{zip_info['status']}`",
        f"- zip file name: `{zip_info['zip_file_name']}`",
        f"- zip path: `{zip_info['zip_path']}`",
        f"- zip SHA-256: `{zip_info['zip_sha256']}`",
        f"- zip size bytes: `{zip_info['size_bytes']}`",
        f"- zip entry count: `{zip_info['entry_count']}`",
        f"- missing required entries: `{len(zip_info['required_missing'])}`",
        f"- cache hits: `{len(zip_info['cache_hits'])}`",
        f"- nested zip hits: `{len(zip_info['nested_zip_hits'])}`",
        f"- local absolute path hits: `{len(zip_info['absolute_path_hits'])}`",
        "",
        "## Protected Result Hashes",
        "",
        "| File | Matches expected | Actual SHA-256 |",
        "|---|---|---|",
        *protected_rows,
        "",
        "## Release Boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in report["release_boundary"])
    lines.extend(["", "## 4A Roadmap Not Executed", ""])
    lines.extend(f"- {item}" for item in report["roadmap_4a_not_executed"])
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", default="", help="Optional final release zip path.")
    parser.add_argument(
        "--validation",
        action="append",
        default=[],
        help="Validation status as name=status. Can be repeated.",
    )
    args = parser.parse_args()
    zip_path = Path(args.zip) if args.zip else None
    report = build_report(zip_path, _parse_validation(args.validation))
    output_dir = root / "artifacts/release"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "final_release_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_markdown(report)
    print("Final release report: artifacts/release/final_release_report.json")
    if report["main_results_modified"]:
        raise SystemExit("main_results hash does not match protected 3C-3 baseline")


if __name__ == "__main__":
    main()
