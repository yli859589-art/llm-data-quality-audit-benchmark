from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.integrity.paths import INTEGRITY, ensure_public_artifact_dirs
from dataaudit_lm.registry.metadata import collect_evidence_summary, summary_as_dict


def main() -> None:
    ensure_public_artifact_dirs()
    summary = collect_evidence_summary()
    checked_paths = [
        ROOT / "README.md",
        ROOT / "docs/PROJECT_OVERVIEW.md",
        ROOT / "docs/RESULTS.md",
        ROOT / "docs/EVIDENCE_SCOPE.md",
        ROOT / "docs/RESUME_PROJECT.md",
    ]
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in checked_paths)
    expected_numbers = [
        summary.source_tokens,
        summary.method_count,
        summary.seed_count,
        summary.completed_runs,
        summary.tokens_per_run,
        summary.total_tokens_seen,
        summary.model_parameters,
    ]
    missing = [number for number in expected_numbers if str(number) not in combined_text]
    forbidden = re.findall(
        r"CCF[-_ ]?[ABC]|CCF[ABC]|TOP[_ -]?TIER|PAPER[_ -]?READY|"
        r"PUBLICATION[_ -]?READY|COMPETITION[_ -]?READY|LEVEL[_ -]?3|LEVEL3|"
        r"SUBMISSION[_ -]?READY|REVIEWER[_ -]?READY",
        combined_text,
    )
    passed = not missing and not forbidden
    payload = {
        "document_consistency_verified": passed,
        "evidence": summary_as_dict(summary),
        "forbidden_readme_terms": sorted(set(forbidden)),
        "checked_documents": [path.relative_to(ROOT).as_posix() for path in checked_paths],
        "missing_readme_numbers": missing,
        "status": "DOCUMENT_CONSISTENCY_VERIFIED" if passed else "DOCUMENT_CONSISTENCY_FAILED",
    }
    write_json(INTEGRITY / "document_consistency_report.json", payload)
    print(
        json.dumps(
            {
                "document_consistency_verified": passed,
                "forbidden_terms": sorted(set(forbidden)),
                "missing_numbers": missing,
            }
        )
    )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
