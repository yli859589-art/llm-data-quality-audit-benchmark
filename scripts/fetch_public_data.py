from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.dataset import load_public_corpus

path = root / "data" / "tinyshakespeare" / "input.txt"
text, source = load_public_corpus(path, allow_download=True)
print(f"Validated {len(text):,} characters at {source.path}")
print(f"SHA-256: {source.sha256}")
