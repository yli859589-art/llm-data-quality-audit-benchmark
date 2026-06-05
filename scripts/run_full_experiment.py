from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.dataset_matrix import (
    dataset_keys_for_mode,
    run_dataset_matrix,
)

rows = run_dataset_matrix(
    root=root,
    output_dir=root / "artifacts" / "dataset_matrix",
    dataset_keys=dataset_keys_for_mode("full"),
    mode="full",
    allow_network=False,
)
print("Full dataset matrix complete")
for row in rows:
    print(f"{row.dataset_key}: {row.status}, fallback={row.used_fallback}, output={row.output_dir}")
