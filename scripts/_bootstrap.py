from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"


def bootstrap() -> None:
    """Make repository-local modules importable from standalone scripts."""
    for path in reversed((str(SRC), str(SCRIPTS))):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)


def build_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    paths = [str(SRC), str(SCRIPTS)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


bootstrap()
