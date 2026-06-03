from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))
analysis = payload.get("error_analysis", {})
examples = analysis.get("sanitized_removed_examples", [])

failure_lines = [
    "# Failure Cases",
    "",
    "These are redacted, truncated examples from documents removed by the full pipeline.",
    "",
]
failure_lines.extend(f"- {example}" for example in examples)
(artifact_dir / "failure_cases.md").write_text("\n".join(failure_lines) + "\n", encoding="utf-8")

error_lines = [
    "# Error Analysis",
    "",
    f"Removed documents: `{analysis.get('removed_documents', 'unknown')}`",
    "",
    "Known quick-mode failure boundaries:",
    "",
    "- Some useful but short text can receive a low length-prior score.",
    "- Standalone HDQS can underperform the raw baseline in this quick run.",
    "- Synthetic web noise is useful for stress testing but not a natural-noise estimate.",
]
(artifact_dir / "error_analysis.md").write_text("\n".join(error_lines) + "\n", encoding="utf-8")
print(f"Failure analysis regenerated in {artifact_dir}")
