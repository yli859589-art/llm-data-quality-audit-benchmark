from __future__ import annotations

from execution_utils import collect_environment, write_report


def main() -> None:
    payload = collect_environment()
    write_report(payload, "step10B_environment_report", "Step 10B Environment Report")
    print(f"Step 10B environment: feasible={payload['heavy_execution_feasible']}")
    if payload["blocking_failures"]:
        print("Blocking failures:")
        for item in payload["blocking_failures"]:
            print(f"- {item}")


if __name__ == "__main__":
    main()

