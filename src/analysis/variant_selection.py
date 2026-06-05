from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


FIELDNAMES = [
    "variant_name",
    "source_artifact",
    "seed_count",
    "mean_ppl_if_available",
    "single_seed_ppl_if_only_debug",
    "delta_vs_raw",
    "delta_vs_random",
    "delta_vs_dedup",
    "keep_rate",
    "train_tokens",
    "evaluated_validation_tokens",
    "selection_reason",
    "risk_note",
    "decision",
]


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _seed1_reference(main_rows: list[dict[str, str]], baseline: str) -> float | None:
    latest = [
        row
        for row in main_rows
        if row.get("baseline_name") == baseline
        and row.get("seed") == "1"
        and row.get("run_status") == "completed_training"
    ]
    if not latest:
        return None
    return _float(latest[-1], "final_val_perplexity")


def _baseline_mean(stats_rows: list[dict[str, str]], baseline: str) -> float | None:
    for row in stats_rows:
        if row.get("baseline_name") == baseline:
            return _float(row, "mean")
    return None


def _format(value: Any) -> str:
    if value in {None, ""}:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def select_variants(
    *,
    ablation_path: Path,
    method_comparison_path: Path,
    diagnostics_path: Path,
    method_debug_path: Path,
    main_results_path: Path,
    stats_main_path: Path,
) -> dict[str, Any]:
    ablation_rows = _read_csv(ablation_path)
    method_rows = _read_csv(method_comparison_path)
    diagnostics_rows = _read_csv(diagnostics_path)
    debug_rows = _read_csv(method_debug_path)
    main_rows = _read_csv(main_results_path)
    stats_rows = _read_csv(stats_main_path)

    raw_ref = _seed1_reference(main_rows, "raw") or _baseline_mean(stats_rows, "raw")
    random_ref = _seed1_reference(main_rows, "random_same_keep_rate") or _baseline_mean(
        stats_rows,
        "random_same_keep_rate",
    )
    dedup_ref = _seed1_reference(main_rows, "dedup_only") or _baseline_mean(
        stats_rows,
        "dedup_only",
    )

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ablation_rows:
        if row.get("run_status") == "completed_training":
            grouped[row.get("ablation_name", "")].append(row)

    v2_full_ppl = None
    if grouped.get("ablation_v2_full"):
        values = [
            _float(row, "final_val_perplexity")
            for row in grouped["ablation_v2_full"]
            if _float(row, "final_val_perplexity") is not None
        ]
        if values:
            v2_full_ppl = mean(values)

    rows: list[dict[str, str]] = []
    for name, group in sorted(grouped.items()):
        values = [
            _float(row, "final_val_perplexity")
            for row in group
            if _float(row, "final_val_perplexity") is not None
        ]
        if not values:
            continue
        seed_count = len({row.get("seed", "") for row in group if row.get("seed")})
        ppl = mean(values)
        keep_rate = _float(group[0], "retention_rate")
        delta_raw = raw_ref - ppl if raw_ref is not None else None
        delta_random = random_ref - ppl if random_ref is not None else None
        delta_dedup = dedup_ref - ppl if dedup_ref is not None else None
        improved_over_full = v2_full_ppl is not None and ppl < v2_full_ppl - 1.0
        close_to_random = delta_random is not None and delta_random > -0.25
        close_to_dedup = delta_dedup is not None and delta_dedup > -0.25
        beats_seed1_raw = delta_raw is not None and delta_raw > 0
        if name == "ablation_v2_without_token_frequency_preservation":
            decision = "promote_to_3seed"
            reason = (
                "Best seed-1 model-training signal; removes the component most likely "
                "to overfit dev token frequencies and improve over raw/random/dedup seed-1 references."
            )
        elif improved_over_full and close_to_random and close_to_dedup:
            decision = "needs_more_diagnostics"
            reason = (
                "Improves strongly over v2 full and is near strong baselines, but the "
                "single seed is not strong enough to promote alongside the best variant."
            )
        elif beats_seed1_raw:
            decision = "needs_more_diagnostics"
            reason = "Seed-1 PPL is promising versus raw but needs component-specific follow-up."
        elif improved_over_full:
            decision = "keep_debug_only"
            reason = "Useful failure diagnosis, but it does not clearly compete with random/dedup."
        else:
            decision = "reject"
            reason = "Does not repair the v2 full failure under the current model-training probe."
        rows.append(
            {
                "variant_name": name,
                "source_artifact": _portable_path(ablation_path),
                "seed_count": str(seed_count),
                "mean_ppl_if_available": _format(ppl if seed_count > 1 else ""),
                "single_seed_ppl_if_only_debug": _format(ppl if seed_count == 1 else ""),
                "delta_vs_raw": _format(delta_raw),
                "delta_vs_random": _format(delta_random),
                "delta_vs_dedup": _format(delta_dedup),
                "keep_rate": _format(keep_rate),
                "train_tokens": group[0].get("train_tokens", ""),
                "evaluated_validation_tokens": group[0].get("evaluated_validation_tokens", ""),
                "selection_reason": reason,
                "risk_note": (
                    "Single-seed diagnostic until rerun under the official 3-seed protocol; "
                    "not a supported method claim."
                ),
                "decision": decision,
            }
        )

    diagnostics = {
        "v2_failure_summary": {
            "method_comparison_rows": method_rows,
            "diagnostic_rows": diagnostics_rows,
            "method_debug_rows": debug_rows,
        },
        "component_diagnosis": [
            {
                "component": "token_frequency_preservation",
                "finding": "Removing it produced the best seed-1 ablation PPL.",
                "action": "Remove from v3 full config.",
            },
            {
                "component": "distribution_preserving_selection",
                "finding": "Strict preservation improved JS diagnostics but not v2 model PPL.",
                "action": "Replace with weak guardrails instead of hard quotas.",
            },
            {
                "component": "length_prior",
                "finding": "Removing length prior improved seed-1 ablation PPL.",
                "action": "Use only a weak length guardrail to avoid extreme shifts.",
            },
            {
                "component": "repetition_penalty",
                "finding": "Removing it helped less than removing token/distribution/length components.",
                "action": "Keep a capped, lower-weight repetition score.",
            },
        ],
        "raw_filtering_risk": (
            "WikiText-2 is already curated; strong document filtering can remove useful "
            "distributional coverage and may be intrinsically hard to beat versus raw."
        ),
    }
    return {"rows": rows, "diagnostics": diagnostics}


def write_variant_outputs(selection: dict[str, Any], *, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = selection["rows"]
    csv_path = output_dir / "promising_variants.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "promising_variants.json").write_text(
        json.dumps(selection, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# Promising Variant Selection",
        "",
        "This table is generated from completed Stage 2.5 diagnostic artifacts. "
        "Single-seed rows are treated as diagnostic signals only.",
        "",
        "| Variant | Decision | Seed count | PPL signal | Reason |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows:
        ppl = row["mean_ppl_if_available"] or row["single_seed_ppl_if_only_debug"]
        lines.append(
            f"| `{row['variant_name']}` | `{row['decision']}` | "
            f"{row['seed_count']} | {ppl} | {row['selection_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Component Diagnosis",
            "",
        ]
    )
    for item in selection["diagnostics"]["component_diagnosis"]:
        lines.append(
            f"- `{item['component']}`: {item['finding']} Action: {item['action']}"
        )
    lines.extend(
        [
            "",
            "## Risk Boundary",
            "",
            selection["diagnostics"]["raw_filtering_risk"],
        ]
    )
    (output_dir / "promising_variants.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
