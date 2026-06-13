from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_mechanism_analysis_v2 import main  # noqa: E402

if __name__ == "__main__":
    if "--analysis" not in sys.argv:
        sys.argv[1:1] = ["--analysis", "proxy_utility"]
    main()

