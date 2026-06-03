from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark import BenchmarkConfig, run_benchmark
from course_project_suite.llm_benchmark.char_lm import TrainConfig

payload = run_benchmark(
    BenchmarkConfig(
        data_path=str(root / "data" / "tinyshakespeare" / "input.txt"),
        output_dir=str(root / "artifacts" / "multi_seed_experiment"),
        mode="multi_seed_debug",
        train_config=TrainConfig(steps=24, eval_interval=6, eval_batches=3),
        seeds=(23, 42, 3407),
    )
)
print("Multi-seed debug experiment complete")
print(f"Variants: {', '.join(payload['model_summary'])}")
