from __future__ import annotations

import os
import shlex
import signal
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path


def command_text(command: Sequence[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline([str(part) for part in command])
    return shlex.join(str(part) for part in command)


def _terminate_process_tree(process: subprocess.Popen[str], env: Mapping[str, str]) -> None:
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=dict(env),
                check=False,
            )
        except FileNotFoundError:
            process.kill()
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
) -> None:
    command_display = command_text(command)
    print(f"RUN {command_display}", flush=True)
    popen_kwargs: dict[str, object] = {
        "cwd": cwd,
        "env": dict(env),
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen([str(part) for part in command], **popen_kwargs)
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        print(f"FAILED {command_display}", flush=True)
        print(f"timeout={timeout}s", flush=True)
        _terminate_process_tree(process, env)
        raise SystemExit(124) from exc

    if returncode != 0:
        print(f"FAILED {command_display}", flush=True)
        print(f"returncode={returncode}", flush=True)
        raise SystemExit(returncode)

    print(f"OK {command_display}", flush=True)


__all__ = ["command_text", "run_command"]
