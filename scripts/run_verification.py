from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
src = str(root / 'src')
env['PYTHONPATH'] = src + os.pathsep + env.get('PYTHONPATH', '')


def run(*args: str) -> None:
    print('+', ' '.join(args), flush=True)
    subprocess.run(args, cwd=root, env=env, check=True)


run(sys.executable, 'all_course_projects.py', '--self-check', '--json')
run(sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v')
run(sys.executable, 'scripts/check_repo.py')
python_files = [str(p.relative_to(root)) for p in root.rglob('*.py') if '__pycache__' not in p.parts]
run(sys.executable, '-m', 'py_compile', *python_files)
print('Full verification workflow: ok')
