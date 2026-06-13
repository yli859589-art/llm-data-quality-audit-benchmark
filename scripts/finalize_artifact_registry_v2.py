from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json
from datetime import datetime, timezone

from artifacts_v2.registry import write_registry
from artifacts_v2.report import write_registry_report
from artifacts_v2.validation import validate_registry_rows
from artifacts_v2.canonical_io import write_canonical_json, write_canonical_text
from experiment_utils import root


def main() -> None:
    registry_path, summary_path, records = write_registry(root)
    rows = [record.to_dict() for record in records]
    errors = validate_registry_rows(rows, root)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report_path = write_registry_report(root, summary)
    payload = {
        "status": "failed" if errors else "passed",
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "registry_path": registry_path.relative_to(root).as_posix(),
        "summary_path": summary_path.relative_to(root).as_posix(),
        "report_path": report_path.relative_to(root).as_posix(),
        "record_count": len(rows),
        "finalized_after_reports": True,
        "hash_check_passed_after_finalization": not errors,
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "artifact_registry_finalization_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json(output, payload)
    md_lines = [
        "# Artifact Registry Finalization Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Finalized after reports: `{payload['finalized_after_reports']}`",
        f"- Hash check passed after finalization: `{payload['hash_check_passed_after_finalization']}`",
        f"- Records: `{payload['record_count']}`",
        "",
        "## Errors",
        "",
    ]
    md_lines.extend([f"- {error}" for error in errors] if errors else ["- none"])
    write_canonical_text(
        root / "artifacts" / "reports" / "artifact_registry_finalization_report.md",
        "\n".join(md_lines),
    )
    if errors:
        raise SystemExit("Artifact registry finalization failed.\n" + "\n".join(errors))
    print(f"Artifact registry v2 finalized: {len(rows)} records")
    print("Artifact registry hash check after finalization: ok")


if __name__ == "__main__":
    main()
