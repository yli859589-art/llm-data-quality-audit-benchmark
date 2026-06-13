from __future__ import annotations


def build_cost_report(
    *,
    runtime_seconds: float,
    input_docs: int,
    kept_docs: int,
    external_dependency_used: bool,
) -> dict[str, object]:
    return {
        "filter_runtime_seconds": runtime_seconds,
        "input_docs": input_docs,
        "kept_docs": kept_docs,
        "estimated_operations": input_docs,
        "external_dependency_used": bool(external_dependency_used),
        "notes": "Step 4 lightweight runtime/cost summary; not a final systems benchmark.",
    }
