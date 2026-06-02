from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Load JSON-compatible YAML without adding a runtime dependency."""
    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{config_path} must use JSON-compatible YAML syntax: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{config_path} must contain a mapping.")
    return payload
