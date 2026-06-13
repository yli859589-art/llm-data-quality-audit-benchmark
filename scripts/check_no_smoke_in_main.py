from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from artifacts_v2.table_linker import smoke_or_protocol_in_main_tables
from experiment_utils import root


def main() -> None:
    errors = [error for error in smoke_or_protocol_in_main_tables(root) if "protocol_only" not in error]
    if errors:
        raise SystemExit("No-smoke-in-main check failed.\n" + "\n".join(errors))
    print("No-smoke-in-main check: ok")


if __name__ == "__main__":
    main()

