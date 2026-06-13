from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from artifacts_v2.hashing import sha256_file
from experiment_utils import root


PROTECTED_FILES = [
    "artifacts/tables/main_results.csv",
    "artifacts/stats/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
    "artifacts/runs/run_registry.jsonl",
]


@dataclass
class CommandRecord:
    command: list[str]
    status: str
    returncode: int | None
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _display(command: list[str]) -> list[str]:
    output = list(command)
    if output and Path(output[0]).resolve() == Path(sys.executable).resolve():
        output[0] = "python"
    return output


def _tail(text: str, limit: int = 8000) -> str:
    return text[-limit:] if len(text) > limit else text


def _run(command: list[str], timeout: int) -> CommandRecord:
    print("RUN " + " ".join(_display(command)), flush=True)
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env=build_subprocess_env(),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        duration = time.perf_counter() - started
        status = "passed" if result.returncode == 0 else "failed"
        if result.stdout:
            print(result.stdout, end="", flush=True)
        if result.stderr:
            print(result.stderr, end="", flush=True)
        print(("OK " if status == "passed" else "FAILED ") + " ".join(_display(command)), flush=True)
        return CommandRecord(
            command=_display(command),
            status=status,
            returncode=result.returncode,
            duration_seconds=duration,
            stdout_tail=_tail(result.stdout or ""),
            stderr_tail=_tail(result.stderr or ""),
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - started
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        print(stdout, end="", flush=True)
        print(stderr, end="", flush=True)
        print(f"FAILED {' '.join(_display(command))}", flush=True)
        print(f"timeout={timeout}s", flush=True)
        return CommandRecord(
            command=_display(command),
            status="timeout",
            returncode=124,
            duration_seconds=duration,
            stdout_tail=_tail(str(stdout)),
            stderr_tail=_tail(str(stderr)),
        )


def _commands(timeout: int) -> list[tuple[list[str], int]]:
    return [
        ([sys.executable, "-m", "pytest", "tests/", "-q"], timeout),
        (
            [
                sys.executable,
                "scripts/run_all_checks.py",
                "--timeout",
                str(timeout),
                "--json-out",
                "artifacts/reports/run_all_checks_report.json",
                "--md-out",
                "artifacts/reports/run_all_checks_report.md",
            ],
            timeout * 8,
        ),
        ([sys.executable, "scripts/check_main_results_purity.py"], timeout),
        ([sys.executable, "scripts/check_claim_hygiene.py"], timeout),
        ([sys.executable, "scripts/check_claim_map.py"], timeout),
        ([sys.executable, "scripts/check_no_forbidden_claims.py"], timeout),
        ([sys.executable, "scripts/check_no_smoke_in_main.py"], timeout),
        ([sys.executable, "scripts/check_no_protocol_as_completed.py"], timeout),
        ([sys.executable, "scripts/check_no_level2_as_level3.py"], timeout),
        ([sys.executable, "scripts/check_level3_gates.py"], timeout),
        ([sys.executable, "scripts/check_registry_to_tables.py"], timeout),
        ([sys.executable, "scripts/check_main_results_from_registry.py"], timeout),
        ([sys.executable, "scripts/check_artifact_registry_v2.py"], timeout),
        ([sys.executable, "scripts/check_filter_manifests.py", "--include-step4"], timeout),
        ([sys.executable, "scripts/check_training_manifests.py", "--include-step5"], timeout),
        ([sys.executable, "scripts/check_urd_manifests.py", "--include-step6"], timeout),
        ([sys.executable, "scripts/check_evaluation_manifests.py", "--include-step7"], timeout),
        ([sys.executable, "scripts/check_mechanism_manifests.py", "--include-step8"], timeout),
        ([sys.executable, "scripts/write_step9_readiness_report.py"], timeout),
    ]


def _protected_hashes() -> dict[str, str]:
    return {path: sha256_file(root / path).upper() for path in PROTECTED_FILES if (root / path).exists()}


def _write_reports(records: list[CommandRecord], started_at: str, started_perf: float) -> dict[str, object]:
    status = "passed"
    if any(record.status == "timeout" for record in records):
        status = "timeout"
    elif any(record.status == "failed" for record in records):
        status = "failed"
    payload = {
        "step": "step9_hotfix",
        "status": status,
        "overall_passed": status == "passed",
        "started_at": started_at,
        "finished_at": _now(),
        "duration_seconds": time.perf_counter() - started_perf,
        "commands": [asdict(record) for record in records],
        "failed_commands": [record.command for record in records if record.status == "failed"],
        "timeout_commands": [record.command for record in records if record.status == "timeout"],
        "protected_hashes": _protected_hashes(),
    }
    out_dir = root / "artifacts" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "step9_hotfix_check_results.json"
    md_path = out_dir / "step9_hotfix_check_results.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Step 9 Hotfix Check Results",
        "",
        f"- Status: `{payload['status']}`",
        f"- Overall passed: `{payload['overall_passed']}`",
        f"- Started at: `{payload['started_at']}`",
        f"- Finished at: `{payload['finished_at']}`",
        f"- Duration seconds: `{payload['duration_seconds']:.3f}`",
        f"- Failed commands: `{len(payload['failed_commands'])}`",
        f"- Timeout commands: `{len(payload['timeout_commands'])}`",
        "",
        "| Command | Status | Return Code | Duration Seconds |",
        "|---|---|---:|---:|",
    ]
    for record in records:
        command = " ".join(record.command).replace("|", "\\|")
        lines.append(f"| `{command}` | `{record.status}` | {record.returncode} | {record.duration_seconds:.3f} |")
    lines.extend(["", "## Output Tails", ""])
    for record in records:
        lines.append("### `" + " ".join(record.command) + "`")
        lines.append("")
        if record.stdout_tail:
            lines.append("```text")
            lines.append(record.stdout_tail.strip())
            lines.append("```")
        if record.stderr_tail:
            lines.append("```text")
            lines.append(record.stderr_tail.strip())
            lines.append("```")
        if not record.stdout_tail and not record.stderr_tail:
            lines.append("_No captured output._")
        lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    started_at = _now()
    started_perf = time.perf_counter()
    records = [_run(command, timeout) for command, timeout in _commands(args.timeout)]
    payload = _write_reports(records, started_at, started_perf)
    print(f"Step 9 hotfix checks: {payload['status']}")
    print("Report: artifacts/reports/step9_hotfix_check_results.json")
    if payload["status"] != "passed":
        raise SystemExit("Step 9 hotfix checks did not pass.")


if __name__ == "__main__":
    main()
