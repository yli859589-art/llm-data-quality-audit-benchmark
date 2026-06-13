from __future__ import annotations

from pathlib import Path
from typing import Any

from .gates import all_gates, current_readiness_from_gates
from .states import ReadinessState


def validate_level3_readiness(root: Path) -> dict[str, Any]:
    gates = all_gates(root)
    current = current_readiness_from_gates(gates)
    return {
        "current_readiness": current,
        "level3_completed_artifact": current == ReadinessState.LEVEL3_COMPLETED_ARTIFACT.value,
        "heavy_execution_completed": False,
        "gates": {name: result.to_dict() for name, result in gates.items()},
    }

