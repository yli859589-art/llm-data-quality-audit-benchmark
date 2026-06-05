from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.config import load_yaml_config
from course_project_suite.llm_benchmark.reporting import write_named_bar_chart

parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode",
    choices=["quick", "paper-prototype", "full"],
    default="quick",
    help="Label the generated scaling artifact; this script does not train models.",
)
args = parser.parse_args()

output_dir = root / "artifacts" / "model_scaling"
output_dir.mkdir(parents=True, exist_ok=True)

rows: list[dict[str, object]] = []
for path in sorted((root / "configs" / "models").glob("*.yaml")):
    config = load_yaml_config(path)
    tokenizer = str(config.get("tokenizer", "character"))
    vocab_size = 128 if "bpe" not in tokenizer.casefold() else 512
    n_embd = int(config.get("n_embd", 32))
    n_layer = int(config.get("n_layer", 1))
    n_head = int(config.get("n_head", 2))
    block_size = int(config.get("block_size", 32))
    estimated_params = vocab_size * n_embd + n_layer * (12 * n_embd * n_embd)
    rows.append(
        {
            "model": config["name"],
            "tokenizer_type": tokenizer,
            "vocab_size_assumption": vocab_size,
            "context_length": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "estimated_parameter_count": estimated_params,
            "fixed_step_budget": "quick=6-8, paper-prototype=10, full=120+",
            "artifact_mode": args.mode,
            "paper_prototype_command": (
                "python scripts/run_multi_seed.py --mode paper-prototype"
                if config["name"] in {"char_tiny_gpt", "char_small_gpt"}
                else "configured_or_dry_run_only"
            ),
            "status": config.get("status", "configured"),
        }
    )

with (output_dir / "model_scaling_summary.csv").open(
    "w", encoding="utf-8", newline=""
) as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

lines = [
    "# Model Scaling Summary",
    "",
    f"Mode label: `{args.mode}`",
    "Seed setting: not applicable; this is generated from model configs.",
    "Training budget: config-level summary only.",
    (
        "Interpretation: this artifact compares configured character/BPE model "
        "sizes and context lengths."
    ),
    (
        "Limitation note: it is not a claim that every model has completed full "
        "training."
    ),
    "",
    "This table is generated from model configs. It is not a claim that every "
    "model has completed full training.",
    "",
    "| Model | Tokenizer | Context | Estimated params | Status |",
    "| --- | --- | ---: | ---: | --- |",
]
for row in rows:
    lines.append(
        f"| `{row['model']}` | {row['tokenizer_type']} | {row['context_length']} | "
        f"{row['estimated_parameter_count']} | {row['status']} |"
    )
(output_dir / "model_scaling_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
write_named_bar_chart(
    output_dir / "scaling_curve.svg",
    [(str(row["model"]), float(row["estimated_parameter_count"])) for row in rows],
    "Configured model scaling",
    "Estimated parameters",
)
print(f"Model scaling artifacts written to {output_dir}")
