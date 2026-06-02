from __future__ import annotations

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark import BenchmarkConfig, run_benchmark
from course_project_suite.llm_benchmark.char_lm import TrainConfig


payload = run_benchmark(
    BenchmarkConfig(
        data_path=str(root / "data" / "tinyshakespeare" / "input.txt"),
        output_dir=str(root / "artifacts" / "full_experiment"),
        mode="full",
        max_documents=140,
        train_chars=52000,
        validation_chars=9000,
        train_config=TrainConfig(),
        seeds=(23, 42, 3407),
        attention_lengths=(32, 64, 128),
        attention_repeats=6,
    )
)
print("Full multi-seed experiment complete")
print(f"Report: {root / 'artifacts' / 'full_experiment' / 'REPORT.md'}")
