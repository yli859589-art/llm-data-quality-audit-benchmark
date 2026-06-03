from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--zip-export",
    action="store_true",
    help="Fail if repository-only metadata such as .git is present.",
)
parser.add_argument(
    "--clean",
    action="store_true",
    help="Remove generated cache files before running strict repository checks.",
)
args = parser.parse_args()

if args.clean:
    from clean_artifacts import clean_generated_paths

    removed = clean_generated_paths(root)
    print(f"Repository cleanup removed {len(removed)} generated cache/temp paths.")

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
    "configs/datasets/synthetic_web_noise.yaml",
    "configs/datasets/local_wikitext_sample.yaml",
    "configs/experiments/baselines.yaml",
    "configs/models/char_tiny_gpt.yaml",
    "configs/models/char_small_gpt.yaml",
    "configs/models/bpe_tiny_gpt.yaml",
    "configs/models/bpe_small_gpt.yaml",
    "configs/models/optional_bpe_medium_gpt.yaml",
    "docs/INTERNAL_AUDIT.md",
    "docs/DATASETS.md",
    "docs/METHOD.md",
    "docs/EXPERIMENTS.md",
    "docs/RESEARCH_READINESS.md",
    "docs/PAPER_DRAFT.md",
    "docs/LIMITATIONS.md",
    "docs/ETHICS.md",
    "docs/REPRODUCIBILITY.md",
    "docs/RESUME.md",
    "docs/FINAL_VERIFICATION_REPORT.md",
    "scripts/run_quick_experiment.py",
    "scripts/run_full_experiment.py",
    "scripts/run_multi_seed.py",
    "scripts/run_dataset_matrix.py",
    "scripts/tune_hdqs_quick.py",
    "scripts/clean_artifacts.py",
    "scripts/make_tables.py",
    "scripts/make_figures.py",
    "scripts/check_artifacts.py",
    "scripts/statistical_analysis.py",
    "scripts/make_research_tables.py",
    "scripts/make_research_figures.py",
    "scripts/analyze_failures.py",
    "scripts/make_project_report.py",
    "scripts/run_model_scaling.py",
    "data/tinyshakespeare/SOURCE.md",
    "data/tinyshakespeare/input.txt",
    "data/samples/synthetic_web_noise.txt",
    "data/samples/local_wikitext_sample.txt",
]
missing = [path for path in required if not (root / path).exists()]
if missing:
    raise SystemExit("Missing required files: " + ", ".join(missing))

dataset = root / "data" / "tinyshakespeare" / "input.txt"
expected_sha256 = "86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed"
actual_sha256 = hashlib.sha256(dataset.read_bytes()).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f"Unexpected Tiny Shakespeare SHA-256: {actual_sha256}")
if args.zip_export and (root / ".git").exists():
    raise SystemExit("ZIP export contains .git metadata.")

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
    "official " + "C" + "MU" + " course project",
    "Car" + "negie " + "Mellon University competition winner",
    "completed Stan" + "ford official coursework",
    "completed Berk" + "eley official coursework",
    "private " + "grader passed",
]:
    if unsupported_claim.casefold() in readme.casefold():
        raise SystemExit(f"README contains unsupported claim: {unsupported_claim}")
institution_terms = ["C" + "MU", "Car" + "negie " + "Mellon"]
for institution_specific in institution_terms:
    if institution_specific.casefold() in readme.casefold():
        raise SystemExit(f"README contains institution-specific claim: {institution_specific}")

all_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in [root / "README.md", root / "docs" / "RESUME.md", root / "docs" / "PAPER_DRAFT.md"]
)
for institution_specific in institution_terms:
    if institution_specific.casefold() in all_text.casefold():
        raise SystemExit(
            f"Documentation contains institution-specific claim: {institution_specific}"
        )

workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
for env_name in ["OMP_NUM_THREADS", "MKL_NUM_THREADS"]:
    if env_name not in workflow:
        raise SystemExit(f"GitHub Actions workflow missing {env_name}")

subprocess.run([sys.executable, "scripts/check_artifacts.py"], cwd=root, check=True)
print("Repository hygiene check: ok")
