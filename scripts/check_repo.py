from pathlib import Path
import subprocess

required = [
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'pyproject.toml',
    'requirements.txt',
    'requirements-dev.txt',
    'all_course_projects.py',
    'src/course_project_suite/run_all.py',
    'src/course_project_suite/cs188/search.py',
    'src/course_project_suite/cs231n/layers.py',
    'src/course_project_suite/cs224n/gpt2.py',
    'src/course_project_suite/cs336/tokenizer.py',
    'docs/PUBLIC_THEME_ALIGNMENT_MATRIX.md',
    'docs/PORTFOLIO_SUMMARY.md',
    'docs/RESUME_BULLETS.md',
    'docs/VERIFICATION_REPORT.md',
    'docs/EXPERIMENT_REPORT.md',
    'docs/ENGINEERING_EVIDENCE.md',
    'docs/COVERAGE_REPORT.txt',
    'docs/BENCHMARK_CARD.md',
    'docs/REFERENCES.md',
    'docs/SUBMISSION_READINESS_CHECKLIST.md',
    'docs/PROVENANCE_AND_ASSISTANCE.md',
    '.github/workflows/ci.yml',
    'tests/test_smoke.py',
    'scripts/run_experiments.py',
    'scripts/fetch_public_data.py',
    'scripts/run_coverage.py',
    'scripts/run_llm_benchmark.py',
    'scripts/run_verification.py',
    'data/tinyshakespeare/SOURCE.md',
    'data/tinyshakespeare/input.txt',
    'artifacts/llm_benchmark/REPORT.md',
    'artifacts/llm_benchmark/results.json',
    'artifacts/llm_benchmark/training_curves.svg',
    'artifacts/llm_benchmark/attention_throughput.svg',
]
missing = [p for p in required if not Path(p).exists()]
if missing:
    raise SystemExit('Missing required files: ' + ', '.join(missing))

try:
    tracked = subprocess.run(
        ['git', 'ls-files'],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
except (FileNotFoundError, subprocess.CalledProcessError):
    tracked = []
bad_cache = [p for p in tracked if '__pycache__' in Path(p).parts or Path(p).suffix == '.pyc']
if bad_cache:
    raise SystemExit('Cache files should not be committed: ' + ', '.join(bad_cache[:10]))

readme = Path('README.md').read_text(encoding='utf-8')
for phrase in ['personal learning and portfolio project', 'does **not** claim', 'Quick start']:
    if phrase not in readme:
        raise SystemExit(f'README missing expected resume-safe phrase: {phrase}')

print('Repository format check: ok')
