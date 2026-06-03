from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
research_dir = root / "artifacts" / "research"
research_dir.mkdir(parents=True, exist_ok=True)
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))
analysis = payload.get("error_analysis", {})
examples = analysis.get("sanitized_removed_examples", [])
seed_setting = ",".join(str(seed) for seed in payload["configuration"]["seeds"])
train_budget = payload["configuration"]["train_chars"]

failure_lines = [
    "# Failure Cases",
    "",
    "Mode: `quick`",
    f"Seed setting: `{seed_setting}`",
    f"Training budget: `{train_budget}` characters per compared variant.",
    (
        "Interpretation: redacted examples illustrate documents removed by the "
        "current full pipeline."
    ),
    (
        "Limitation note: examples are truncated diagnostics, not manually "
        "adjudicated labels."
    ),
    "",
]
failure_lines.extend(f"- {example}" for example in examples)
(artifact_dir / "failure_cases.md").write_text("\n".join(failure_lines) + "\n", encoding="utf-8")
(research_dir / "failure_cases.md").write_text(
    "\n".join(failure_lines) + "\n", encoding="utf-8"
)

error_lines = [
    "# Error Analysis",
    "",
    "Mode: `quick`",
    f"Seed setting: `{seed_setting}`",
    f"Training budget: `{train_budget}` characters per compared variant.",
    (
        "Interpretation: this file records known failure boundaries from the "
        "current compact run."
    ),
    (
        "Limitation note: larger datasets and human-reviewed categories are "
        "required before paper-level error analysis."
    ),
    "",
    f"Removed documents: `{analysis.get('removed_documents', 'unknown')}`",
    "",
    "Known quick-mode failure boundaries:",
    "",
    "- Some useful but short text can receive a low length-prior score.",
    "- Standalone HDQS can underperform the raw baseline in compact runs.",
    "- Synthetic web noise is a reproducible stress test, not a natural-noise estimate.",
]
(artifact_dir / "error_analysis.md").write_text("\n".join(error_lines) + "\n", encoding="utf-8")
(research_dir / "error_analysis.md").write_text("\n".join(error_lines) + "\n", encoding="utf-8")
print(f"Failure analysis regenerated in {artifact_dir} and {research_dir}")
