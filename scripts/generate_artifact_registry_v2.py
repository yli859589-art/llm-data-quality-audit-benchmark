from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from artifacts_v2.registry import write_registry
from artifacts_v2.report import write_registry_report
from experiment_utils import root


def main() -> None:
    registry_path, summary_path, _records = write_registry(root)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report_path = write_registry_report(root, summary)
    print(f"Artifact registry v2 records: {summary['record_count']}")
    print(f"Registry: {registry_path.relative_to(root).as_posix()}")
    print(f"Summary: {summary_path.relative_to(root).as_posix()}")
    print(f"Report: {report_path.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()

