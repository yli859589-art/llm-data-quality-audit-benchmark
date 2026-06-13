from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path
from typing import Any

from experiment_utils import root
from filters_v2.manifest import sha256_file
from filters_v2.validation import FilterManifestError, validate_filter_manifest
from training_v2.validation import assert_training_outputs_not_in_main_results


URD_REQUIRED_HASHES = {
    "component_scores.jsonl",
    "urd_summary.json",
    "selected_doc_ids.jsonl",
    "decisions.jsonl",
    "scores.jsonl",
    "keep_rate_report.json",
    "risk_report.json",
    "diversity_report.json",
    "cost_report.json",
}

WEIGHT_FIELDS = {"alpha", "beta", "gamma", "lambda_shift", "mu_cost"}


def _resolve(path: str, package_root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else package_root / value


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _check_no_main_results_pollution() -> None:
    assert_training_outputs_not_in_main_results(root)
    forbidden_tokens = ["filter_outputs_step6", "urd_fixed", "urd_pareto", "urd_ablation"]
    for path in [
        root / "artifacts" / "tables" / "main_results.csv",
        root / "artifacts" / "stats" / "main_results.csv",
        root / "artifacts" / "cross_dataset" / "cross_dataset_results.csv",
    ]:
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        for token in forbidden_tokens:
            if token in text:
                raise FilterManifestError(f"URD smoke output leaked into {path.relative_to(root).as_posix()}")


def validate_urd_manifest(manifest: dict[str, Any], package_root: Path) -> None:
    validate_filter_manifest(manifest, package_root)
    if manifest.get("method_family") != "URD-Selector":
        raise FilterManifestError("URD manifest must set method_family=URD-Selector")
    if manifest.get("level3_main_method_candidate") is not True:
        raise FilterManifestError("URD manifest must mark level3_main_method_candidate=true")
    if manifest.get("verified_effectiveness") is not False:
        raise FilterManifestError("URD manifest must set verified_effectiveness=false")
    if manifest.get("scope") == "smoke" and manifest.get("smoke_only") is not True:
        raise FilterManifestError("URD smoke manifest must set smoke_only=true")
    proxy_components = manifest.get("proxy_components")
    if not isinstance(proxy_components, list) or not proxy_components:
        raise FilterManifestError("URD manifest must record non-empty proxy_components")
    if manifest.get("no_model_training_run") is not True:
        raise FilterManifestError("URD manifest must record no_model_training_run=true")
    if manifest.get("no_ppl_or_downstream_result_added") is not True:
        raise FilterManifestError("URD manifest must record no_ppl_or_downstream_result_added=true")
    output_hashes = manifest.get("output_hashes")
    if not isinstance(output_hashes, dict):
        raise FilterManifestError("URD output_hashes must be an object")
    missing = sorted(URD_REQUIRED_HASHES - set(output_hashes))
    if missing:
        raise FilterManifestError("URD output_hashes missing files: " + ", ".join(missing))
    for name, info in output_hashes.items():
        path = _resolve(str(info.get("path", "")), package_root)
        if not path.exists():
            raise FilterManifestError(f"URD output missing: {path}")
        if sha256_file(path) != info.get("sha256"):
            raise FilterManifestError(f"URD output hash mismatch: {path}")
    summary = _load_json(_resolve(output_hashes["urd_summary.json"]["path"], package_root))
    if summary.get("verified_effectiveness") is not False:
        raise FilterManifestError("urd_summary must set verified_effectiveness=false")
    rows = _read_jsonl(_resolve(output_hashes["component_scores.jsonl"]["path"], package_root))
    if not rows:
        raise FilterManifestError("component_scores.jsonl is empty")
    for row in rows:
        for field in ["utility_score", "risk_score", "diversity_score", "shift_penalty", "cost_score"]:
            value = row.get(field)
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                raise FilterManifestError(f"component score out of [0, 1]: {field}")
    mode = manifest.get("selection_mode")
    if mode == "fixed_weight":
        weights = manifest.get("weights")
        if not isinstance(weights, dict) or not WEIGHT_FIELDS.issubset(weights):
            raise FilterManifestError("fixed-weight URD manifest missing weights")
    elif mode == "pareto":
        if "pareto_frontier.csv" not in output_hashes or "pareto_layers.json" not in output_hashes:
            raise FilterManifestError("pareto URD manifest missing Pareto outputs")
        if manifest.get("pareto_proxy_used") is not True:
            raise FilterManifestError("pareto URD manifest must set pareto_proxy_used=true")
        objectives = manifest.get("pareto_objectives")
        if not isinstance(objectives, list) or not objectives:
            raise FilterManifestError("pareto URD manifest missing objectives")
    else:
        raise FilterManifestError(f"unsupported URD selection_mode: {mode}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 6 URD manifests.")
    parser.add_argument("--path", default="artifacts/filter_outputs_step6")
    parser.add_argument("--include-step6", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base = root / args.path if not Path(args.path).is_absolute() else Path(args.path)
    manifests = sorted(base.glob("**/filter_manifest.json")) if base.exists() else []
    errors: list[str] = []
    for path in manifests:
        try:
            validate_urd_manifest(_load_json(path), root)
        except (json.JSONDecodeError, FilterManifestError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = path.as_posix()
            errors.append(f"{label}: {exc}")
    if args.include_step6 and not manifests:
        errors.append("No Step 6 URD manifests found.")
    try:
        _check_no_main_results_pollution()
    except FilterManifestError as exc:
        errors.append(str(exc))
    report = {
        "status": "failed" if errors else "passed",
        "checked_manifests": len(manifests),
        "include_step6": bool(args.include_step6),
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "urd_manifest_check_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("URD manifest check failed.\n" + "\n".join(errors))
    print(f"URD manifest check: ok ({len(manifests)} manifests)")


if __name__ == "__main__":
    main()
