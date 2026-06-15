from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.integrity.paths import INTEGRITY

BUNDLE = Path.home() / "Desktop" / "backup_pre_dataaudit_refactor_20260613.bundle"
EXPECTED_RESTORABLE_SHA = "16b33e8e6fc97be1c0f3475abb23ea8ced9571c8"
WINDOWS_GIT = (
    Path(os.environ.get("ProgramFiles", ""))
    / "Microsoft Visual Studio"
    / "2022"
    / "Community"
    / "Common7"
    / "IDE"
    / "CommonExtensions"
    / "Microsoft"
    / "TeamFoundation"
    / "Team Explorer"
    / "Git"
    / "cmd"
    / "git.exe"
)


def _git() -> str:
    found = shutil.which("git")
    if found:
        return found
    if WINDOWS_GIT.exists():
        return str(WINDOWS_GIT)
    raise RuntimeError("git executable not found")


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def _sanitize(text: str) -> str:
    return text.replace(str(BUNDLE), "<desktop-bundle>").replace(
        str(BUNDLE).replace("\\", "/"), "<desktop-bundle>"
    )


def main() -> None:
    git = _git()
    INTEGRITY.mkdir(parents=True, exist_ok=True)
    verify = _run([git, "bundle", "verify", str(BUNDLE)], cwd=ROOT)
    restored_head = ""
    branches: list[str] = []
    log_lines: list[str] = []
    cleanup_success = False
    clone_returncode: int | None = None
    with tempfile.TemporaryDirectory(prefix="dataaudit_backup_restore_") as tmp:
        restore_dir = Path(tmp) / "backup_restore_test"
        clone = _run([git, "clone", str(BUNDLE), str(restore_dir)], cwd=ROOT)
        clone_returncode = clone.returncode
        if clone.returncode == 0:
            head = _run([git, "rev-parse", "HEAD"], cwd=restore_dir)
            branch_proc = _run([git, "branch", "--all"], cwd=restore_dir)
            log_proc = _run([git, "log", "--oneline", "-5"], cwd=restore_dir)
            restored_head = head.stdout.strip()
            branches = [line.strip() for line in branch_proc.stdout.splitlines() if line.strip()]
            log_lines = [line.strip() for line in log_proc.stdout.splitlines() if line.strip()]
        tmp_path = Path(tmp)
    cleanup_success = not tmp_path.exists()
    payload = {
        "bundle_path": "Desktop/backup_pre_dataaudit_refactor_20260613.bundle",
        "bundle_exists": BUNDLE.exists(),
        "bundle_verify_returncode": verify.returncode,
        "bundle_verify_stdout": _sanitize(verify.stdout),
        "bundle_verify_stderr": _sanitize(verify.stderr),
        "clone_returncode": clone_returncode,
        "restored_head": restored_head,
        "branches": branches,
        "log_oneline_5": log_lines,
        "expected_restorable_sha": EXPECTED_RESTORABLE_SHA,
        "expected_sha_restorable": EXPECTED_RESTORABLE_SHA
        in "\n".join(log_lines + [restored_head]),
        "restore_successful": verify.returncode == 0
        and clone_returncode == 0
        and bool(restored_head),
        "temporary_restore_dir_cleaned": cleanup_success,
    }
    write_json(INTEGRITY / "backup_restore_report.json", payload)
    print(json.dumps({"restore_successful": payload["restore_successful"], "head": restored_head}))
    if not payload["restore_successful"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
