from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.config import load_yaml_config


def _write_md_table(path: Path, title: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text(f"# {title}\n\nNo rows available.\n", encoding="utf-8")
        return
    columns = list(rows[0])
    lines = [f"# {title}", "", "| " + " | ".join(columns) + " |"]
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


artifact_dir = root / "artifacts" / "quick_experiment"
dataset_dir = root / "artifacts" / "dataset_matrix"
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))

_write_md_table(
    artifact_dir / "multi_dataset_results_table.md",
    "Multi-Dataset Results Table",
    _read_csv(dataset_dir / "dataset_matrix_summary.csv"),
)
_write_md_table(
    artifact_dir / "multi_seed_results_table.md",
    "Multi-Seed Results Table",
    _read_csv(artifact_dir / "aggregated_results.csv"),
)
_write_md_table(
    artifact_dir / "privacy_utility_table.md",
    "Privacy Utility Table",
    _read_csv(artifact_dir / "privacy_utility_tradeoff.csv"),
)
_write_md_table(
    artifact_dir / "downstream_table.md",
    "Downstream Table",
    _read_csv(artifact_dir / "downstream_results.csv"),
)
tests = json.loads((artifact_dir / "statistical_tests.json").read_text(encoding="utf-8"))
stat_rows = [
    {"comparison": name, **value}
    for name, value in tests.get("paired", {}).items()
    if isinstance(value, dict)
]
_write_md_table(artifact_dir / "statistical_tests_table.md", "Statistical Tests", stat_rows)

model_rows: list[dict[str, object]] = []
for config_path in sorted((root / "configs" / "models").glob("*.yaml")):
    config = load_yaml_config(config_path)
    vocab_size = 96 if "bpe" not in str(config.get("tokenizer", "")).casefold() else 512
    n_embd = int(config.get("n_embd", 32))
    n_layer = int(config.get("n_layer", 1))
    estimated_params = vocab_size * n_embd + n_layer * (12 * n_embd * n_embd)
    model_rows.append(
        {
            "model": config["name"],
            "tokenizer": config["tokenizer"],
            "vocab_size_assumption": vocab_size,
            "estimated_parameter_count": estimated_params,
            "block_size": config.get("block_size"),
            "status": config.get("status", "configured"),
        }
    )
with (artifact_dir / "model_scaling_summary.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(model_rows[0]))
    writer.writeheader()
    writer.writerows(model_rows)
_write_md_table(artifact_dir / "model_scaling_table.md", "Model Scaling Table", model_rows)
_write_md_table(artifact_dir / "model_scaling_summary.md", "Model Scaling Summary", model_rows)

failure_rows = payload.get("error_analysis", {}).get("sanitized_removed_examples", [])
(artifact_dir / "failure_cases.md").write_text(
    "# Failure Cases\n\n"
    + "\n\n".join(f"- {example}" for example in failure_rows)
    + "\n\nExamples are redacted and truncated.\n",
    encoding="utf-8",
)
print(f"Research tables regenerated in {artifact_dir}")
