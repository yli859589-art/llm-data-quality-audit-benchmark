from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
research_dir = root / "artifacts" / "research"
research_dir.mkdir(parents=True, exist_ok=True)
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))
hdqs = payload.get("hdqs_sweep_report", {})
seed_setting = ",".join(str(seed) for seed in payload["configuration"]["seeds"])
train_budget = payload["configuration"]["train_chars"]

lines = [
    "# Project Report",
    "",
    "This generated report summarizes the current research prototype artifacts.",
    "",
    "## Positioning",
    "",
    "Resume-ready and CCF-C-convertible research prototype; not a completed paper.",
    "",
    "## Quick Evidence",
    "",
    f"- Mode: `{payload['mode']}`",
    f"- Seed setting: `{seed_setting}`",
    f"- Training budget: `{train_budget}` characters per compared variant",
    f"- Dataset: `{payload['dataset']['dataset_name']}`",
    f"- HDQS standalone status: `{hdqs.get('standalone_hdqs_status', 'unknown')}`",
    f"- Trained variants: `{', '.join(payload['model_summary'])}`",
    "",
    "Interpretation: quick-mode results validate reproducibility and instrumentation.",
    "Limitation note: compact results are not paper-level model-quality evidence.",
    "",
    "## Generated Tables",
    "",
    "- `main_results_table.md`",
    "- `multi_dataset_results_table.md`",
    "- `multi_seed_results_table.md`",
    "- `privacy_utility_table.md`",
    "- `downstream_table.md`",
    "- `statistical_tests_table.md`",
    "",
    "## Generated Figures",
    "",
    "- `retention_vs_perplexity.svg`",
    "- `privacy_vs_utility.svg`",
    "- `pipeline_order_comparison.svg`",
    "- `model_scaling_curve.svg`",
    "- `hdqs_sweep_heatmap.svg`",
    "- `privacy_retention_pareto.svg`",
    "",
    "## Remaining Full Experiments",
    "",
    "- Run explicit-network or local WikiText-2/OpenWebText/C4 samples.",
    "- Scale full mode across larger datasets, longer budgets, and model sizes.",
    "- Tune HDQS++ weights on a development split.",
]
(artifact_dir / "project_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

readiness = [
    "# Research Readiness Summary",
    "",
    "Generated from current repository artifacts.",
    "",
    (
        f"Mode: `{payload['mode']}` for quick artifacts; `paper-prototype` "
        "for dataset and multi-seed artifacts."
    ),
    (
        f"Seed setting: `{seed_setting}` for quick artifacts; `23,42,3407` "
        "for paper-prototype multi-seed."
    ),
    f"Training budget: `{train_budget}` quick-mode characters per compared variant.",
    (
        "Interpretation: the repository is executable, reproducible, and "
        "research-convertible."
    ),
    (
        "Limitation note: it remains a research prototype until full external "
        "dataset experiments and longer training are complete."
    ),
    "",
    "## Implemented",
    "",
    "- HDQS++ / DQCS diagnostics",
    "- baseline and ablation matrix",
    "- real local paper-prototype dataset matrix small runs",
    "- optional remote dataset fallback reports",
    "- three-seed statistical analysis artifacts",
    "- model-scaling config artifacts",
    "- privacy-utility and downstream artifacts",
    "",
    "## Current Evidence Boundary",
    "",
    (
        "Quick and paper-prototype results validate reproducibility, instrumentation, "
        "and experiment wiring. Multi-seed intervals are still wide, so they should "
        "not be presented as paper-level model-quality evidence."
    ),
    "",
    "## Required Before Paper Submission",
    "",
    "- Run explicit-network or local WikiText-2/OpenWebText/C4 experiments.",
    "- Run full-mode training with longer budgets and multiple model scales.",
    "- Freeze tuned HDQS++ weights on a development split.",
    "- Add deeper manual failure taxonomy and privacy testing.",
]
(artifact_dir / "research_readiness_summary.md").write_text(
    "\n".join(readiness) + "\n", encoding="utf-8"
)
(research_dir / "research_readiness_summary.md").write_text(
    "\n".join(readiness) + "\n", encoding="utf-8"
)
print(f"Project report regenerated: {artifact_dir / 'project_report.md'}")
