from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root
from readiness_v2.gates import scan_forbidden_claims


def main() -> None:
    findings = scan_forbidden_claims(root)
    report = {
        "status": "failed" if findings else "passed",
        "forbidden_claims_found": len(findings),
        "findings": findings,
    }
    output = root / "artifacts" / "reports" / "forbidden_claims_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if findings:
        lines = [f"{item['file']}:{item['line']} {item['text']}" for item in findings]
        raise SystemExit("Forbidden claim check failed.\n" + "\n".join(lines))
    print("Forbidden claim check: ok")


if __name__ == "__main__":
    main()

