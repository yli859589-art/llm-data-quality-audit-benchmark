from __future__ import annotations

import csv
from pathlib import Path

from experiment_utils import load_json_yaml, root


def _check_config(path: Path) -> list[str]:
    config = load_json_yaml(path)
    errors = []
    if config.get("mode") in {"paper", "full"}:
        if config.get("allow_fallback_in_data") is not False:
            errors.append(f"{path} allows fallback in paper/full mode")
        if config.get("required_real_data") is not True:
            errors.append(f"{path} does not require real data")
    if path.name.endswith("_paper.yaml"):
        if config.get("allow_fallback") is not False:
            errors.append(f"{path} allows dataset fallback")
        if config.get("required_real_data") is not True:
            errors.append(f"{path} is not marked required_real_data")
        if config.get("is_smoke") is True:
            errors.append(f"{path} is marked smoke")
    return errors


def main() -> None:
    errors: list[str] = []
    for path in list((root / "configs" / "experiments").glob("paper*.yaml")) + [
        root / "configs" / "experiments" / "full_all.yaml"
    ]:
        errors.extend(_check_config(path))
    for path in (root / "configs" / "data").glob("*_paper.yaml"):
        errors.extend(_check_config(path))

    registry_path = root / "artifacts" / "runs" / "run_registry.csv"
    if registry_path.exists():
        with registry_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("mode") in {"paper", "full"} and row.get("used_fallback") == "True":
                    errors.append(f"Paper/full registry row used fallback: {row.get('run_id')}")
    if errors:
        raise SystemExit("Fallback experiment check failed." + "\n" + "\n".join(errors))
    print("No-fallback experiment check: ok")


if __name__ == "__main__":
    main()
