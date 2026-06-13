from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root
from readiness_v2.validator import validate_level3_readiness


def main() -> None:
    report = validate_level3_readiness(root)
    errors = []
    if report["level3_completed_artifact"] is True:
        errors.append("current readiness cannot be LEVEL3_COMPLETED_ARTIFACT before Step 10B/10C heavy execution")
    for path in sorted((root / "artifacts" / "reports").glob("*readiness_report.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("level3_completed_artifact") is True:
            errors.append(f"{path.relative_to(root).as_posix()} sets level3_completed_artifact=true")
        if payload.get("current_readiness") == "LEVEL3_COMPLETED_ARTIFACT":
            errors.append(f"{path.relative_to(root).as_posix()} sets current_readiness=LEVEL3_COMPLETED_ARTIFACT")
    if errors:
        raise SystemExit("No-Level2-as-Level3 check failed.\n" + "\n".join(errors))
    print("No-Level2-as-Level3 check: ok")


if __name__ == "__main__":
    main()

