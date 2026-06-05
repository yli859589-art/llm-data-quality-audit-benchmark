from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark import BenchmarkConfig, run_benchmark
from course_project_suite.llm_benchmark.char_lm import TrainConfig

parser = argparse.ArgumentParser()
parser.add_argument("--quick", action="store_true", help="Run a smaller CI-friendly benchmark.")
parser.add_argument("--device", default="cpu")
parser.add_argument("--output-dir", default=str(root / "artifacts" / "quick_experiment"))
args = parser.parse_args()

train = (
    TrainConfig(steps=8, eval_interval=4, eval_batches=2, n_embd=24)
    if args.quick
    else TrainConfig()
)
config = BenchmarkConfig(
    data_path=str(root / "data" / "tinyshakespeare" / "input.txt"),
    output_dir=args.output_dir,
    mode="quick" if args.quick else "full_single_seed",
    max_documents=60 if args.quick else 140,
    train_chars=18000 if args.quick else 52000,
    validation_chars=5000 if args.quick else 9000,
    train_config=train,
    attention_lengths=(32, 64) if args.quick else (32, 64, 128),
    attention_repeats=3 if args.quick else 6,
    device=args.device,
)
payload = run_benchmark(config)
models = payload["language_model_ablation"]
print("LLM benchmark complete")
for name, metrics in models.items():
    print(
        f"{name}: val_loss={metrics['final_val_loss']:.4f}, "
        f"perplexity={metrics['final_val_perplexity']:.2f}"
    )
print(f"Report: {Path(args.output_dir) / 'REPORT.md'}")
