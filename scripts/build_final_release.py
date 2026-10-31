"""Build and verify a source-only final release ZIP without historical mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def tracked_files(root: Path) -> list[Path]:
    completed = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    return [root / item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def build(root: Path, output: Path) -> dict[str, object]:
    files = [path for path in tracked_files(root) if path.is_file()]
    manifest = {
        "release_format": "p2-02.source-only.v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "raw_corpora_included": False,
        "binary_checkpoints_included": False,
        "data_status": "BLOCKED_BY_MISSING_DATA: formal C4/OpenWebText shards are not included.",
        "files": {path.relative_to(root).as_posix(): sha256(path) for path in files},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
        archive.writestr(
            "RELEASE_MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
    with zipfile.ZipFile(output) as archive:
        corrupt = archive.testzip()
        names = set(archive.namelist())
        if corrupt or not {
            "README.md",
            "scripts/quality_system.py",
            "apps/quality_system_app.py",
            "RELEASE_MANIFEST.json",
        }.issubset(names):
            raise RuntimeError(
                f"release verification failed: corrupt={corrupt}, required files missing"
            )
    with tempfile.TemporaryDirectory(prefix="p2-02-release-") as directory:
        target = Path(directory)
        with zipfile.ZipFile(output) as archive:
            archive.extractall(target)
        probe = subprocess.run(
            [sys.executable, "scripts/quality_system.py", "--help"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0 or "Unified command-line interface" not in probe.stdout:
            raise RuntimeError(f"extracted CLI verification failed: {probe.stderr or probe.stdout}")
        extracted_manifest = json.loads(
            (target / "RELEASE_MANIFEST.json").read_text(encoding="utf-8")
        )
        if len(extracted_manifest["files"]) != len(files):
            raise RuntimeError("extracted manifest file count mismatch")
    return {
        "zip": str(output.resolve()),
        "sha256": sha256(output),
        "bytes": output.stat().st_size,
        "tracked_files": len(files),
        "zip_integrity": "pass",
        "extracted_cli": "pass",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output", type=Path, default=Path("dist/llm-data-quality-curation-p2-02.zip")
    )
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    report = args.report if args.report.is_absolute() else root / args.report
    result = build(root, output)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
