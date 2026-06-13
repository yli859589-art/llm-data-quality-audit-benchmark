from __future__ import annotations

from typing import Any

VALID_COMPONENTS = {"utility", "risk", "diversity", "shift", "cost"}


def disabled_components_from_name(name: str) -> set[str]:
    prefix = "urd_ablation_no_"
    if not name.startswith(prefix):
        return set()
    component = name.removeprefix(prefix)
    return {component} if component in VALID_COMPONENTS else set()


def disabled_components_from_config(config: dict[str, Any], filter_name: str) -> set[str]:
    configured = config.get("disabled_components", [])
    disabled = {str(item) for item in configured if str(item) in VALID_COMPONENTS}
    disabled.update(disabled_components_from_name(filter_name))
    return disabled
