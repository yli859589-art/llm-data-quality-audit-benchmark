from __future__ import annotations

import json

from experiment_utils import root


def _exists(path: str) -> bool:
    return (root / path).exists()


def _count_registry_rows() -> int:
    path = root / "artifacts" / "runs" / "run_registry.csv"
    if not path.exists():
        return 0
    return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)


def _has_real_nonfallback_manifest() -> bool:
    for path in (root / "artifacts" / "data").glob("*/data_manifest.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("required_real_data") and not payload.get("used_fallback"):
            return True
    return False


def main() -> None:
    checks = {
        "data_configs": all(
            _exists(path)
            for path in [
                "configs/data/wikitext2_smoke.yaml",
                "configs/data/wikitext2_paper.yaml",
                "configs/data/openwebtext_smoke.yaml",
                "configs/data/openwebtext_paper.yaml",
                "configs/data/c4_en_smoke.yaml",
                "configs/data/c4_en_paper.yaml",
            ]
        ),
        "experiment_configs": all(
            _exists(path)
            for path in [
                "configs/experiments/smoke.yaml",
                "configs/experiments/dev.yaml",
                "configs/experiments/paper_wikitext2.yaml",
                "configs/experiments/paper_openwebtext.yaml",
                "configs/experiments/paper_c4.yaml",
                "configs/experiments/full_all.yaml",
            ]
        ),
        "smoke_manifest": _exists("artifacts/data/wikitext2_smoke/data_manifest.json"),
        "baseline_registry_rows": _count_registry_rows(),
        "frozen_protocol_artifact": _exists("artifacts/frozen/hdqspp_frozen_wikitext2_smoke.json"),
        "ablation_artifact": _exists("artifacts/ablations/smoke/ablation_results.csv"),
        "significance_artifact": _exists("artifacts/stats/claim_safety_report.md"),
        "tables_figures": _exists("artifacts/tables/baseline_comparison.md")
        and _exists("artifacts/figures/baseline_retention.svg"),
        "real_nonfallback_manifest": _has_real_nonfallback_manifest(),
    }
    hard_missing = [
        name
        for name, value in checks.items()
        if name not in {"baseline_registry_rows", "real_nonfallback_manifest"} and not value
    ]
    level = "FAIL" if hard_missing else "PROTOTYPE"
    if (
        not hard_missing
        and checks["real_nonfallback_manifest"]
        and checks["baseline_registry_rows"]
    ):
        level = "EXPERIMENT-CANDIDATE"
    if level == "EXPERIMENT-CANDIDATE":
        level_reason = "Infrastructure and at least one real non-fallback manifest exist."
    elif level == "PROTOTYPE":
        level_reason = "Smoke/dev infrastructure exists, but real paper-scale runs are incomplete."
    else:
        level_reason = "Required smoke/dev artifacts are missing."
    report = {
        "readiness_level": level,
        "level_reason": level_reason,
        "checks": checks,
        "hard_missing": hard_missing,
        "ccf_c_ready": False,
        "remaining_to_ccf_c_ready": [
            "Complete non-fallback WikiText-2/OpenWebText/C4 data preparation.",
            "Run multi-seed model training with validation/perplexity metrics.",
            "Run paper-scale ablations and statistical tests on held-out test splits.",
            "Attach compute logs, environment hashes, and reviewer-facing failure analysis.",
        ],
    }
    output_json = root / "artifacts" / "experiment_readiness_report.json"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md = [
        "# Experiment Readiness Report",
        "",
        f"- Readiness level: `{level}`",
        f"- Reason: {level_reason}",
        f"- CCF-C experiment ready: `{report['ccf_c_ready']}`",
        "",
        "## Checks",
        "",
    ]
    for name, value in checks.items():
        md.append(f"- `{name}`: `{value}`")
    md.extend(["", "## Remaining Work", ""])
    md.extend(f"- {item}" for item in report["remaining_to_ccf_c_ready"])
    (root / "docs" / "EXPERIMENT_READINESS_REPORT.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )
    print(f"Experiment readiness: {level}")
    print(f"Report: {output_json}")
    if level == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
