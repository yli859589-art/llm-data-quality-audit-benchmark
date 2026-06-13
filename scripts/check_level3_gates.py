from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from experiment_utils import root
from readiness_v2.report import write_level3_gate_reports
from readiness_v2.validator import validate_level3_readiness


def main() -> None:
    report = validate_level3_readiness(root)
    write_level3_gate_reports(root, report)
    claim_gate = report["gates"]["claim_gate"]
    if claim_gate["status"] != "pass":
        raise SystemExit("Level 3 gate check failed because ClaimGate failed.")
    print("Level 3 gates checked:")
    for name, gate in report["gates"].items():
        print(f"- {name}: {gate['status']}")
    print(f"Overall readiness: {report['current_readiness']}")


if __name__ == "__main__":
    main()

