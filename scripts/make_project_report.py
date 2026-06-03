from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))
hdqs = payload.get("hdqs_sweep_report", {})

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
    f"- Dataset: `{payload['dataset']['dataset_name']}`",
    f"- HDQS standalone status: `{hdqs.get('standalone_hdqs_status', 'unknown')}`",
    f"- Trained variants: `{', '.join(payload['model_summary'])}`",
    "",
    "## Generated Tables",
    "",
    "- `main_results_table.md`",
    "- `multi_dataset_results_table.md`",
    "- `multi_seed_results_table.md`",
    "- `privacy_utility_table.md`",
    "- `downstream_table.md`",
    "",
    "## Generated Figures",
    "",
    "- `retention_vs_perplexity.svg`",
    "- `privacy_vs_utility.svg`",
    "- `pipeline_order_comparison.svg`",
    "- `model_scaling_curve.svg`",
    "",
    "## Remaining Full Experiments",
    "",
    "- Run explicit-network or local WikiText-2/OpenWebText/C4 samples.",
    "- Run paper-prototype and full modes across three seeds.",
    "- Tune HDQS++ weights on a development split.",
]
(artifact_dir / "project_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Project report regenerated: {artifact_dir / 'project_report.md'}")
