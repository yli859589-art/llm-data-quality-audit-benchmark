from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = build_subprocess_env()


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=root, env=env, check=True)


run(sys.executable, "scripts/fetch_public_data.py")
run(sys.executable, "all_course_projects.py", "--self-check", "--json")
run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
python_files = [
    str(p.relative_to(root)) for p in root.rglob("*.py") if "__pycache__" not in p.parts
]
run(sys.executable, "-m", "py_compile", *python_files)
print("Full verification workflow: ok")
