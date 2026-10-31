"""Manifest-first, resumable HTTP fetcher for P1-2 corpus shards.

It defaults to a no-network plan.  Supplying --execute is an explicit action;
the completed file is accepted only when its SHA-256 matches --sha256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform the network transfer; otherwise only write a plan",
    )
    args = parser.parse_args()
    target = Path(args.output).resolve()
    if "evaluation_step7" in target.parts:
        raise ValueError("refusing to place downloaded data in a historical evidence directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    plan = {
        "url": args.url,
        "output": str(target),
        "expected_sha256": args.sha256.upper(),
        "resume": True,
        "executed": args.execute,
    }
    plan_path = target.with_suffix(target.suffix + ".fetch-plan.json")
    if not args.execute:
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(f"plan only; no download started: {plan_path}")
        return
    offset = target.stat().st_size if target.exists() else 0
    request = Request(args.url, headers={"Range": f"bytes={offset}-"} if offset else {})
    with urlopen(request) as response, target.open("ab" if offset else "wb") as handle:
        if offset and getattr(response, "status", None) != 206:
            raise RuntimeError(
                "server did not honour byte-range resume; remove the partial file only after inspecting it"
            )
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            handle.write(chunk)
    actual = sha256(target)
    if actual != args.sha256.upper():
        raise ValueError(f"SHA-256 mismatch for {target}: {actual}")
    plan.update({"actual_sha256": actual, "bytes": target.stat().st_size, "executed": True})
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"verified: {target}")


if __name__ == "__main__":
    main()
