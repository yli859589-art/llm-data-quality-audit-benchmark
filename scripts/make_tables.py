from __future__ import annotations

import argparse
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--artifact-dir", default="artifacts/quick_experiment")
args = parser.parse_args()
output = root / args.artifact_dir
payload = json.loads((output / "results.json").read_text(encoding="utf-8"))

summary_lines = [
    "# Main Results Table",
    "",
    f"Generated from `{args.artifact_dir}/results.json` in `{payload['mode']}` mode.",
    "",
    (
        "Quick mode is a CPU, single-seed smoke test. The table verifies "
        "reproducibility and instrumentation; it is not model-quality evidence "
        "or a paper-level result."
    ),
    "",
    (
        "| Variant | Validation loss mean +/- std | Perplexity mean +/- std | "
        "BPC | Next-char accuracy |"
    ),
    "| --- | ---: | ---: | ---: | ---: |",
]
for name, row in payload["model_summary"].items():
    summary_lines.append(
        f"| `{name}` | {row['final_val_loss']['mean']:.4f} +/- "
        f"{row['final_val_loss']['std']:.4f} | "
        f"{row['final_val_perplexity']['mean']:.2f} +/- {row['final_val_perplexity']['std']:.2f} | "
        f"{row['final_val_bits_per_character']['mean']:.3f} | "
        f"{row['final_val_next_char_accuracy']['mean']:.3f} |"
    )
(output / "main_results_table.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

ablation_lines = [
    "# Data Intervention Ablation Table",
    "",
    "| Variant | Documents | Characters | Duplicate rate | PII-like hits | Mean HDQS |",
    "| --- | ---: | ---: | ---: | ---: | ---: |",
]
for name, row in payload["data_quality_ablation"].items():
    pii = row["email_hits"] + row["phone_hits"] + row["id_like_hits"]
    ablation_lines.append(
        f"| `{name}` | {row['documents']} | {row['characters']} | "
        f"{row['duplicate_rate']:.3f} | {pii} | {row['mean_hdqs']:.3f} |"
    )
(output / "ablation_table.md").write_text("\n".join(ablation_lines) + "\n", encoding="utf-8")
hdqs = payload.get("hdqs_sweep_report", {})
note = [
    "# HDQS Interpretation Note",
    "",
    hdqs.get(
        "interpretation",
        (
            "Standalone HDQS should be interpreted as a pipeline component "
            "until larger experiments validate it."
        ),
    ),
    "",
    f"Standalone status: `{hdqs.get('standalone_hdqs_status', 'unknown')}`",
]
(output / "hdqs_interpretation_note.md").write_text("\n".join(note) + "\n", encoding="utf-8")
print(f"Tables regenerated in {output}")
