from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root


def main() -> None:
    errors = []
    for path in sorted((root / "artifacts").glob("**/*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("protocol_only") is True and payload.get("completed") is True:
            errors.append(path.relative_to(root).as_posix())
        if "downstream_protocol" in path.as_posix().casefold() and payload.get("completed") is True:
            errors.append(path.relative_to(root).as_posix() + " marks downstream protocol completed")
    if errors:
        raise SystemExit("No-protocol-as-completed check failed.\n" + "\n".join(errors))
    print("No-protocol-as-completed check: ok")


if __name__ == "__main__":
    main()

