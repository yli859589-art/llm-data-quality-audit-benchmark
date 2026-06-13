from __future__ import annotations

from localmax_utils import collect_localmax_environment, write_report


def main() -> None:
    payload = collect_localmax_environment()
    write_report(payload, "localmax_environment_report", "LocalMax Environment Report")
    print(f"LocalMax environment: feasible={payload['localmax_feasible']}")
    for item in payload["blocking_failures"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()

