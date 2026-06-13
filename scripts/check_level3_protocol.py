from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from experiment_utils import root
from level3.protocol_utils import validate_protocol, write_report


def main() -> None:
    payload = validate_protocol()
    write_report(
        payload,
        root / "artifacts" / "reports" / "level3_protocol_check_report.json",
        root / "artifacts" / "reports" / "level3_protocol_check_report.md",
        "Level 3 Protocol Check Report",
    )
    if payload["status"] != "passed":
        raise SystemExit("Level 3 protocol check failed.\n" + "\n".join(payload["errors"]))
    print("Level 3 protocol check: ok")


if __name__ == "__main__":
    main()

