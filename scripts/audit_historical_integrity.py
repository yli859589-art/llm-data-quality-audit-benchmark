"""Read-only hash audit for legacy manifests; never rewrites historical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def audit(root: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    findings = []
    for path_key, hash_key in (("metrics_path", "metrics_hash"), ("report_path", "report_hash")):
        relative = str(manifest.get(path_key, ""))
        expected = str(manifest.get(hash_key, "")).upper()
        path = root / relative
        actual = sha256(path) if path.is_file() else ""
        findings.append(
            {
                "path_field": path_key,
                "hash_field": hash_key,
                "path": relative,
                "exists": path.is_file(),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "match": bool(actual and actual == expected),
            }
        )
    return {
        "audit_version": "p2-02.historical-integrity.v1",
        "mode": "read_only",
        "manifest": manifest_path.relative_to(root).as_posix(),
        "findings": findings,
        "status": "pass" if all(item["match"] for item in findings) else "fail",
        "remediation": (
            "Historical evidence is preserved. Generate new versioned output rather than "
            "rewriting a mismatched legacy manifest."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/evaluation_step7/downstream_protocol/evaluation_manifest.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    report = audit(root, manifest)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output)}))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
