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


def _read_csv(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_md_table(
    path: Path,
    title: str,
    rows: list[dict[str, object]],
    metadata: list[str],
) -> None:
    lines = [f"# {title}", "", *metadata, ""]
    if not rows:
        lines.append("No rows available.")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    columns = list(rows[0])
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_table_both(
    filename: str,
    title: str,
    rows: list[dict[str, object]],
    metadata: list[str],
) -> None:
    _write_md_table(artifact_dir / filename, title, rows, metadata)
    _write_md_table(research_dir / filename, title, rows, metadata)


artifact_dir = root / "artifacts" / "quick_experiment"
research_dir = root / "artifacts" / "research"
dataset_dir = root / "artifacts" / "dataset_matrix"
multi_seed_dir = root / "artifacts" / "multi_seed"
research_dir.mkdir(parents=True, exist_ok=True)

payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))
seed_setting = ",".join(str(seed) for seed in payload["configuration"]["seeds"])
train_budget = payload["configuration"]["train_chars"]
common_metadata = [
    f"Mode: `{payload['mode']}` unless a table explicitly references paper-prototype.",
    f"Seed setting: `{seed_setting}` for quick artifacts; `23,42,3407` for multi-seed.",
    f"Training budget: `{train_budget}` characters per compared quick-mode variant.",
    (
        "Interpretation: generated evidence for reproducibility, diagnostics, "
        "and research-readiness inspection."
    ),
    (
        "Limitation note: quick and paper-prototype results are preliminary; "
        "full multi-dataset, longer-budget runs are still required."
    ),
]

_write_table_both(
    "multi_dataset_results_table.md",
    "Multi-Dataset Results Table",
    _read_csv(dataset_dir / "paper_prototype_summary.csv"),
    [
        "Mode: `paper-prototype` dataset matrix.",
        "Seed setting: dataset-matrix small runs use the configured paper-prototype seed.",
        "Training budget: compact paper-prototype character budget per dataset.",
        (
            "Interpretation: local rows demonstrate executable dataset-matrix "
            "runs; fallback rows only document unavailable optional datasets."
        ),
        "Limitation note: fallback rows are not remote-dataset model results.",
    ],
)
_write_table_both(
    "multi_seed_results_table.md",
    "Multi-Seed Results Table",
    _read_csv(multi_seed_dir / "aggregated_results.csv"),
    [
        "Mode: `paper-prototype` multi-seed.",
        "Seed setting: `23,42,3407`.",
        "Training budget: compact paper-prototype budget per seed/variant.",
        (
            "Interpretation: aggregate rows show direction and variance across "
            "seeds, not final paper-level significance."
        ),
        "Limitation note: confidence intervals are wide in the current small run.",
    ],
)
_write_table_both(
    "privacy_utility_table.md",
    "Privacy Utility Table",
    _read_csv(artifact_dir / "privacy_utility_tradeoff.csv"),
    common_metadata,
)
_write_table_both(
    "downstream_table.md",
    "Downstream Table",
    _read_csv(artifact_dir / "downstream_results.csv"),
    common_metadata,
)

tests = json.loads((multi_seed_dir / "statistical_tests.json").read_text(encoding="utf-8"))
stat_rows = [
    {"comparison": name, **value}
    for name, value in tests.get("paired", {}).items()
    if isinstance(value, dict)
]
_write_table_both(
    "statistical_tests_table.md",
    "Statistical Tests",
    stat_rows,
    [
        "Mode: `paper-prototype` paired comparisons.",
        "Seed setting: `23,42,3407`.",
        "Training budget: compact paper-prototype budget per seed/variant.",
        (
            "Interpretation: positive mean improvement means lower perplexity for "
            "the candidate, but interval width must be inspected."
        ),
        "Limitation note: current intervals are not strong enough for final paper claims.",
    ],
)

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
_write_table_both(
    "model_scaling_table.md",
    "Model Scaling Table",
    model_rows,
    [
        "Mode: config-level model scaling summary.",
        "Seed setting: not applicable.",
        "Training budget: not a training run.",
        (
            "Interpretation: compares configured character/BPE model sizes and "
            "context lengths."
        ),
        "Limitation note: this table does not claim full training for every model.",
    ],
)
_write_md_table(
    artifact_dir / "model_scaling_summary.md",
    "Model Scaling Summary",
    model_rows,
    [
        "Mode: config-level model scaling summary.",
        "Seed setting: not applicable.",
        "Training budget: not a training run.",
        "Interpretation: generated from model config files.",
        "Limitation note: not all listed configs are trained in quick or CI.",
    ],
)

failure_rows = payload.get("error_analysis", {}).get("sanitized_removed_examples", [])
(artifact_dir / "failure_cases.md").write_text(
    "# Failure Cases\n\n"
    "Mode: `quick`\n"
    f"Seed setting: `{seed_setting}`\n"
    f"Training budget: `{train_budget}` characters per compared variant.\n"
    "Interpretation: examples illustrate removed-text diagnostics.\n"
    "Limitation note: examples are redacted, truncated, and not human labels.\n\n"
    + "\n\n".join(f"- {example}" for example in failure_rows)
    + "\n",
    encoding="utf-8",
)
print(f"Research tables regenerated in {artifact_dir} and {research_dir}")
