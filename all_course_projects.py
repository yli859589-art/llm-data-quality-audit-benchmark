#!/usr/bin/env python3
"""Compatibility entry point for the public-course-inspired implementation suite."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from course_project_suite.run_all import main

if __name__ == "__main__":
    main()
