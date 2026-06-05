from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

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
    "MANIFEST.md",
    "RELEASE_NOTES.md",
    "VERSION",
    "PROJECT_SUMMARY.md",
    "PROJECT_ONE_PAGE.md",
    "TECHNICAL_OVERVIEW.md",
    "DEMO_GUIDE.md",
    "RESUME_BULLETS.md",
    "Makefile",
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
    "configs/experiments/smoke.yaml",
    "configs/experiments/dev.yaml",
    "configs/experiments/method_debug.yaml",
    "configs/experiments/paper_wikitext2.yaml",
    "configs/experiments/paper_openwebtext.yaml",
    "configs/experiments/paper_c4.yaml",
    "configs/experiments/full_all.yaml",
    "configs/data/wikitext2_smoke.yaml",
    "configs/data/wikitext2_paper.yaml",
    "configs/data/openwebtext_smoke.yaml",
    "configs/data/openwebtext_paper.yaml",
    "configs/data/c4_en_smoke.yaml",
    "configs/data/c4_en_paper.yaml",
    "configs/models/char_tiny_gpt.yaml",
    "configs/models/char_small_gpt.yaml",
    "configs/models/bpe_tiny_gpt.yaml",
    "configs/models/bpe_small_gpt.yaml",
    "configs/models/optional_bpe_medium_gpt.yaml",
    "configs/models/tiny.yaml",
    "configs/models/small.yaml",
    "configs/models/medium.yaml",
    "configs/filters/hdqspp_v2.yaml",
    "configs/filters/hdqspp_v3.yaml",
    "configs/frozen/hdqspp_global.yaml",
    "configs/frozen/hdqspp_frozen_wikitext2.yaml",
    "configs/frozen/hdqspp_v2_frozen_wikitext2.yaml",
    "configs/frozen/hdqspp_v3_frozen_wikitext2.yaml",
    "configs/frozen/hdqspp_frozen_openwebtext.yaml",
    "configs/frozen/hdqspp_frozen_c4.yaml",
    "docs/INTERNAL_AUDIT.md",
    "docs/FINAL_AUDIT.md",
    "docs/README.md",
    "docs/QUICKSTART.md",
    "docs/PROJECT_STATUS.md",
    "docs/PROJECT_PRESENTATION_NOTES.md",
    "docs/EXPERIMENT_DASHBOARD.md",
    "docs/METHOD_DIAGNOSTICS.md",
    "docs/METHOD_DASHBOARD.md",
    "docs/PROJECT_EVIDENCE_MAP.md",
    "docs/BENCHMARK_PROTOCOL.md",
    "docs/ARTIFACT_INDEX.md",
    "docs/FAILURE_CASES.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/FRESH_CLONE_TEST.md",
    "docs/future_publication_notes/README.md",
    "docs/future_publication_notes/CCF_C_EXPERIMENT_GAP_AUDIT.md",
    "docs/EXPERIMENT_READINESS_REPORT.md",
    "docs/CLAIM_ARTIFACT_MAP.md",
    "docs/CLAIM_ARTIFACT_MAP.csv",
    "docs/future_publication_notes/REVIEWER_ATTACK_REPORT.md",
    "docs/future_publication_notes/PAPER_NOTES.md",
    "docs/RELATED_WORK_NOTES.md",
    "docs/BIBLIOGRAPHY.bib",
    "docs/DATASETS.md",
    "docs/METHOD.md",
    "docs/EXPERIMENTS.md",
    "docs/RESEARCH_READINESS.md",
    "docs/future_publication_notes/PAPER_DRAFT.md",
    "docs/future_publication_notes/SUBMISSION_READINESS_CHECKLIST.md",
    "docs/LIMITATIONS.md",
    "docs/ETHICS.md",
    "docs/REPRODUCIBILITY.md",
    "docs/REPORTING_CONTRACT.md",
    "docs/FIGURE_INDEX.md",
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
    "scripts/run_experiment.py",
    "scripts/prepare_real_data.py",
    "scripts/run_baselines.py",
    "scripts/model_summary.py",
    "scripts/freeze_hdqspp.py",
    "scripts/run_ablation.py",
    "scripts/analyze_significance.py",
    "scripts/generate_tables.py",
    "scripts/generate_figures.py",
    "scripts/diagnose_hdqspp.py",
    "scripts/run_method_debug.py",
    "scripts/freeze_hdqspp_v2.py",
    "scripts/run_model_ablation.py",
    "scripts/analyze_method_errors.py",
    "scripts/select_promising_variants.py",
    "scripts/freeze_hdqspp_v3.py",
    "scripts/run_variant_experiments.py",
    "scripts/run_v3_ablation.py",
    "scripts/generate_method_dashboard.py",
    "scripts/generate_project_dashboard.py",
    "scripts/run_all_checks.py",
    "scripts/run_minimal_benchmark.py",
    "scripts/run_audit_benchmark.py",
    "scripts/run_release_checks.py",
    "scripts/clean_project_artifacts.py",
    "scripts/check_no_fallback_in_experiments.py",
    "scripts/check_claims_supported.py",
    "scripts/check_claim_hygiene.py",
    "scripts/verify_fresh_unzip.py",
    "scripts/generate_final_release_report.py",
    "scripts/check_experiment_readiness.py",
    "scripts/check_registry_schema.py",
    "scripts/check_artifact_lineage.py",
    "scripts/check_main_results_purity.py",
    "scripts/check_training_budget_thresholds.py",
    "scripts/check_config_not_downgraded.py",
    "scripts/check_split_integrity.py",
    "scripts/check_no_test_leakage.py",
    "scripts/registry_utils.py",
    "scripts/capture_environment.py",
    "src/analysis/quality_error_analysis.py",
    "src/analysis/variant_selection.py",
    "src/diagnostics/hdqspp_failure.py",
    "src/filters/hdqspp_v2.py",
    "src/filters/hdqspp_v3.py",
    "src/filters/scoring_calibration.py",
    "data/tinyshakespeare/SOURCE.md",
    "data/tinyshakespeare/input.txt",
    "data/samples/synthetic_web_noise.txt",
    "data/samples/local_wikitext_sample.txt",
    "artifacts/release/fresh_unzip_report.json",
    "artifacts/release/fresh_unzip_report.md",
    "artifacts/release/final_release_report.json",
    "artifacts/release/final_release_report.md",
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
    relative = path.relative_to(root).as_posix()
    is_allowed_real_data = relative.startswith("data/real/wikitext2_raw/")
    if path.is_file() and path.stat().st_size > 5 * 1024 * 1024 and not is_allowed_real_data:
        large_files.append(path.relative_to(root).as_posix())
if cache_paths:
    if args.clean:
        removed = clean_generated_paths(root)
        if removed:
            print(f"Repository cleanup removed {len(removed)} late cache/temp paths.")
        cache_paths = []
        for path in root.rglob("*"):
            if ".git" in path.parts:
                continue
            if path.name in cache_names or "__pycache__" in path.parts or path.suffix == ".pyc":
                cache_paths.append(path.relative_to(root).as_posix())
    if cache_paths:
        raise SystemExit("Remove cache files before verification: " + ", ".join(cache_paths[:10]))
if large_files:
    raise SystemExit("Repository contains files larger than 5 MiB: " + ", ".join(large_files))

absolute_path = re.compile(
    rf"(?:(?<![A-Za-z])[A-Za-z]:(?:\\+|/(?!/))|/{'Users'}/|/{'home'}/[^/]+/|/"
    + "mnt"
    + "/"
    + "data"
    + "/|/"
    + "tmp"
    + "/)"
)
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
    for path in [root / "README.md", root / "docs" / "RESUME.md"]
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

subprocess.run([sys.executable, "scripts/check_artifacts.py"], cwd=root, env=build_subprocess_env(), check=True)
print("Repository hygiene check: ok")
