from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .evidence import EvidenceRequirement, status_from_requirements
from .states import ReadinessState


FORBIDDEN_CLAIM_PATTERNS = [
    r"\bURD(?:-Selector)?\s+beats\s+raw\b",
    r"\bURD(?:-Selector)?\s+outperforms\s+raw\b",
    r"\bURD(?:-Selector)?\s+improves\s+PPL\b",
    r"\bURD(?:-Selector)?\s+improves\s+downstream\b",
    r"\bSOTA\b",
    r"\bstate[- ]of[- ]the[- ]art\b",
    r"\bCCF-B\s+ready\b",
    r"\bCCF-A\s+ready\b",
    r"\bLevel\s+3\s+completed\b",
    r"\bLEVEL3_COMPLETED_ARTIFACT\b",
    r"\b500M\s+tokens\s+completed\b",
    r"\b1B\s+tokens\s+completed\b",
    r"\bofficial\s+C4\s+reproduction\b",
    r"\bofficial\s+Gopher\s+reproduction\b",
    r"\bofficial\s+CCNet\s+reproduction\b",
    r"\bmedium\s+model\s+completed\b",
    r"\blarge-lite\s+completed\b",
    r"\bdownstream\s+completed\b",
    r"\bmechanism\s+proved\b",
    r"\bPareto\s+frontier\s+improved\b",
]

ALLOWED_CONTEXT_MARKERS = [
    "not yet",
    "not completed",
    "not currently",
    "not ready",
    "not main evidence",
    "not allowed",
    "not established",
    "not ccf-b ready",
    "not ccf-c ready",
    "not a completed",
    "future target",
    "future/conditional",
    "future-only",
    "protocol-only",
    "allowed only after",
    "disallowed claim",
    "forbidden claim",
    "forbidden claims",
    "forbidden current claim",
    "forbidden items",
    "forbidden until",
    "only a completed",
    "claim boundary",
    "unsupported",
    "false",
]


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    passed: bool
    summary: str
    requirements: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _json_files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _requirement(name: str, present: bool, notes: str, required: bool = True) -> EvidenceRequirement:
    return EvidenceRequirement(name=name, required=required, present=present, notes=notes)


def data_gate(root: Path) -> GateResult:
    manifests = [_load_json(path) for path in _json_files(root, "artifacts/**/data_manifest.json")]
    heavy = [
        manifest
        for manifest in manifests
        if not manifest.get("smoke_only")
        and not manifest.get("fallback_used", False)
        and int(manifest.get("bpe_tokens", manifest.get("token_count", 0)) or 0) >= 500_000_000
    ]
    requirements = [
        _requirement("at_least_three_real_large_datasets", len(heavy) >= 3, "Requires >=3 real datasets."),
        _requirement("each_dataset_min_500m_bpe_tokens", len(heavy) >= 3, "Requires tokenizer-specific BPE counts."),
        _requirement("no_fallback", all(not item.get("fallback_used", False) for item in heavy) and bool(heavy), "Fallback must be false."),
        _requirement("split_integrity", len(heavy) >= 3, "Split integrity must be recorded for heavy data."),
    ]
    return GateResult(
        "DataGate",
        status_from_requirements(requirements),
        False,
        "No verified 500M-token Level 3 data matrix is present.",
        [asdict(item) for item in requirements],
        ["Smoke/sample/protocol data cannot satisfy Level 3 data readiness."],
    )


def tokenizer_gate(root: Path) -> GateResult:
    manifests = [_load_json(path) for path in _json_files(root, "artifacts/**/tokenizer_manifest.json")]
    has_smoke_bpe = any("bpe" in str(item.get("tokenizer_type", "")).casefold() for item in manifests)
    has_mainline = any(
        str(item.get("tokenizer_type", "")).casefold() in {"gpt2", "bpe32k", "bpe16k"}
        and not item.get("smoke_only", False)
        for item in manifests
    )
    requirements = [
        _requirement("bpe_or_gpt2_mainline", has_mainline, "GPT-2 or BPE16k/BPE32k mainline tokenizer required."),
        _requirement("lightweight_bpe_smoke_available", has_smoke_bpe, "Smoke BPE is useful but not Level 3 mainline.", False),
    ]
    return GateResult(
        "TokenizerGate",
        "partial" if has_smoke_bpe and not has_mainline else status_from_requirements(requirements),
        has_mainline,
        "Only smoke/prototype tokenizer evidence is available.",
        [asdict(item) for item in requirements],
        ["Char or lightweight BPE smoke tokenization cannot satisfy Level 3 tokenizer readiness."],
    )


def filter_gate(root: Path) -> GateResult:
    manifests = [_load_json(path) for path in _json_files(root, "artifacts/**/filter_manifest.json")]
    names = {str(item.get("filter_name", "")).casefold() for item in manifests}
    required = {
        "raw",
        "random_same_keep_rate",
        "exact_dedup",
        "length_filter",
        "c4_style",
        "gopher_style",
        "ccnet_style",
        "perplexity",
        "embedding",
        "urd_fixed",
        "urd_pareto",
    }
    present = {name for name in required if any(name in existing for existing in names)}
    requirements = [_requirement(name, name in present, "Required Level 3 filter/baseline family.") for name in sorted(required)]
    return GateResult(
        "FilterGate",
        "partial" if present else "not_ready",
        False,
        "Filter interface artifacts exist, but the full Level 3 matrix has not run on heavy data.",
        [asdict(item) for item in requirements],
        ["Proxy filters and smoke outputs do not satisfy full baseline authenticity."],
    )


def model_scale_gate(root: Path) -> GateResult:
    manifests = [_load_json(path) for path in _json_files(root, "artifacts/**/training_manifest.json")]
    scale_classes = {str(item.get("scale_class", "")).casefold() for item in manifests if item.get("completed")}
    requirements = [
        _requirement("small_completed", "small" in scale_classes, "Small model training must be real completed evidence."),
        _requirement("medium_completed", "medium" in scale_classes, "Medium model training is required."),
        _requirement("selected_large_lite_completed", "large_lite" in scale_classes or "large-lite" in scale_classes, "Selected large-lite runs are required."),
        _requirement("tiny_smoke_available", any("tiny" in item for item in scale_classes), "Tiny smoke is not Level 3 evidence.", False),
    ]
    return GateResult(
        "ModelScaleGate",
        "partial" if manifests else "not_ready",
        False,
        "Only smoke/prototype training evidence is available.",
        [asdict(item) for item in requirements],
        ["Tiny/smoke training cannot satisfy Level 3 model-scale readiness."],
    )


def evaluation_gate(root: Path) -> GateResult:
    manifests = [_load_json(path) for path in _json_files(root, "artifacts/**/evaluation_manifest.json")]
    types = {str(item.get("evaluation_type", "")).casefold() for item in manifests}
    requirements = [
        _requirement("lm_metrics", "lm" in types, "LM metrics interface must exist."),
        _requirement("official_downstream_completed", False, "Requires 3-5 real downstream benchmark completions."),
        _requirement("risk_diversity_cost", {"risk", "diversity", "cost"}.issubset(types), "Risk/diversity/cost evaluators must exist."),
        _requirement("pareto", "pareto" in types, "Pareto evaluator must exist."),
        _requirement("statistics_stability_completed", False, "Stability is currently protocol/smoke only."),
    ]
    return GateResult(
        "EvaluationGate",
        "partial" if manifests else "not_ready",
        False,
        "Evaluation infrastructure exists; official downstream and full matrix are not completed.",
        [asdict(item) for item in requirements],
        ["Protocol-only downstream cannot be reported as completed."],
    )


def mechanism_gate(root: Path) -> GateResult:
    manifests = [_load_json(path) for path in _json_files(root, "artifacts/**/mechanism_manifest.json")]
    types = {str(item.get("analysis_type", "")).casefold() for item in manifests}
    required = {
        "proxy_utility",
        "overfiltering",
        "diversity_loss",
        "domain_shift",
        "rank_stability",
        "tokenizer_sensitivity",
        "scale_trend",
        "failure_taxonomy",
        "pareto_mechanism",
    }
    requirements = [_requirement(name, name in types, "Mechanism analysis family present.") for name in sorted(required)]
    return GateResult(
        "MechanismGate",
        "partial" if manifests else "not_ready",
        False,
        "Mechanism infrastructure exists, but full-scale mechanism evidence is not completed.",
        [asdict(item) for item in requirements],
        ["Smoke/protocol mechanism diagnostics cannot be reported as full-scale conclusions."],
    )


def _line_context(lines: list[str], index: int) -> str:
    start = max(0, index - 5)
    end = min(len(lines), index + 4)
    return " ".join(line.strip() for line in lines[start:end]).casefold()


def scan_forbidden_claims(root: Path) -> list[dict[str, Any]]:
    files = [root / "README.md"]
    files.extend(sorted((root / "docs").rglob("*.md")) if (root / "docs").exists() else [])
    findings: list[dict[str, Any]] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in FORBIDDEN_CLAIM_PATTERNS]
    for path in files:
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            for pattern, regex in zip(FORBIDDEN_CLAIM_PATTERNS, compiled):
                if not regex.search(line):
                    continue
                context = _line_context(lines, index)
                if any(marker in context for marker in ALLOWED_CONTEXT_MARKERS):
                    continue
                findings.append(
                    {
                        "file": path.relative_to(root).as_posix(),
                        "line": index + 1,
                        "pattern": pattern,
                        "text": line.strip(),
                    }
                )
    return findings


def claim_gate(root: Path) -> GateResult:
    findings = scan_forbidden_claims(root)
    return GateResult(
        "ClaimGate",
        "pass" if not findings else "fail",
        not findings,
        "Forbidden promotional claims are absent or appear only in boundary/negative contexts.",
        [],
        [f"{item['file']}:{item['line']} {item['text']}" for item in findings],
    )


def all_gates(root: Path) -> dict[str, GateResult]:
    gates = {
        "data_gate": data_gate(root),
        "tokenizer_gate": tokenizer_gate(root),
        "filter_gate": filter_gate(root),
        "model_scale_gate": model_scale_gate(root),
        "evaluation_gate": evaluation_gate(root),
        "mechanism_gate": mechanism_gate(root),
        "claim_gate": claim_gate(root),
    }
    return gates


def current_readiness_from_gates(gates: dict[str, GateResult]) -> str:
    if not gates["claim_gate"].passed:
        return ReadinessState.EXPERIMENT_CANDIDATE.value
    return ReadinessState.LEVEL3_PIPELINE_READY.value
