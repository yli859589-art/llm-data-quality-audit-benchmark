from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
required = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "CHANGELOG.md",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    ".pre-commit-config.yaml",
    "ruff.toml",
    "mypy.ini",
    ".github/workflows/ci.yml",
    "configs/datasets/tiny_shakespeare.yaml",
    "configs/datasets/wikitext2.yaml",
    "configs/datasets/openwebtext_sample.yaml",
    "configs/datasets/c4_sample.yaml",
    "configs/datasets/mixed_debug.yaml",
    "docs/INTERNAL_AUDIT.md",
    "docs/DATASETS.md",
    "docs/METHOD.md",
    "docs/EXPERIMENTS.md",
    "docs/PAPER_DRAFT.md",
    "docs/LIMITATIONS.md",
    "docs/ETHICS.md",
    "docs/REPRODUCIBILITY.md",
    "docs/RESUME.md",
    "docs/FINAL_VERIFICATION_REPORT.md",
    "scripts/run_quick_experiment.py",
    "scripts/run_full_experiment.py",
    "scripts/run_multi_seed.py",
    "scripts/make_tables.py",
    "scripts/make_figures.py",
    "scripts/check_artifacts.py",
    "data/tinyshakespeare/SOURCE.md",
    "data/tinyshakespeare/input.txt",
]
missing = [path for path in required if not (root / path).exists()]
if missing:
    raise SystemExit("Missing required files: " + ", ".join(missing))

dataset = root / "data" / "tinyshakespeare" / "input.txt"
expected_sha256 = "86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed"
actual_sha256 = hashlib.sha256(dataset.read_bytes()).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f"Unexpected Tiny Shakespeare SHA-256: {actual_sha256}")

cache_names = {".coverage", "coverage.xml", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
cache_paths = []
large_files = []
for path in root.rglob("*"):
    if ".git" in path.parts:
        continue
    if path.name in cache_names or "__pycache__" in path.parts or path.suffix == ".pyc":
        cache_paths.append(path.relative_to(root).as_posix())
    if path.is_file() and path.stat().st_size > 5 * 1024 * 1024:
        large_files.append(path.relative_to(root).as_posix())
if cache_paths:
    raise SystemExit("Remove cache files before verification: " + ", ".join(cache_paths[:10]))
if large_files:
    raise SystemExit("Repository contains files larger than 5 MiB: " + ", ".join(large_files))

absolute_path = re.compile(rf"(?:[A-Za-z]:(?:\\+|/(?!/))|/{'Users'}/|/{'home'}/[^/]+/)")
text_suffixes = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".py", ".toml", ".cff"}
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "data" in path.parts:
        continue
    if path.suffix.lower() not in text_suffixes and path.name not in {".gitignore"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if absolute_path.search(text):
        raise SystemExit(f"Absolute local path found: {path.relative_to(root)}")

readme = (root / "README.md").read_text(encoding="utf-8")
for phrase in [
    "personal research and portfolio prototype",
    "does **not** claim",
    "Quick Start",
    "single-seed",
]:
    if phrase not in readme:
        raise SystemExit(f"README missing required boundary phrase: {phrase}")
for unsupported_claim in [
    "CCF-C accepted paper",
    "official CMU course project",
    "Carnegie Mellon University competition winner",
]:
    if unsupported_claim.casefold() in readme.casefold():
        raise SystemExit(f"README contains unsupported claim: {unsupported_claim}")

subprocess.run([sys.executable, "scripts/check_artifacts.py"], cwd=root, check=True)
print("Repository hygiene check: ok")
