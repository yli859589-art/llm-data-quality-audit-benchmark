from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .keep_rate import compute_document_keep_rate, compute_token_keep_rate


def estimate_tokens(text: str) -> int:
    return len(text.split())


@dataclass(frozen=True)
class FilterInput:
    doc_id: str
    text: str
    source: str = ""
    split: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 0

    @classmethod
    def from_mapping(cls, row: dict[str, Any], index: int = 0) -> "FilterInput":
        text = str(row.get("text", ""))
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        estimated = row.get("estimated_tokens")
        try:
            estimated_tokens = int(estimated)
        except (TypeError, ValueError):
            estimated_tokens = estimate_tokens(text)
        return cls(
            doc_id=str(row.get("doc_id") or f"doc-{index}"),
            text=text,
            source=str(row.get("source", "")),
            split=str(row.get("split", "")),
            metadata=dict(metadata),
            estimated_tokens=estimated_tokens,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FilterConfig:
    filter_name: str
    filter_type: str
    target_keep_rate: float | None = None
    token_budget: int | None = None
    token_counter_type: str = "whitespace_proxy"
    seed: int = 42
    scope: str = "smoke"
    dataset_name: str = ""
    dataset_manifest_path: str = ""
    tokenizer_manifest_path: str = ""
    allow_external_dependency: bool = False
    allow_proxy: bool = False
    smoke_only: bool = True
    notes: str = ""
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FilterDecision:
    doc_id: str
    keep: bool
    score: float
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FilterResult:
    filter_name: str
    filter_type: str
    input_docs: int
    kept_docs: int
    input_estimated_tokens: int
    kept_estimated_tokens: int
    document_keep_rate: float
    token_keep_rate: float
    decisions: list[FilterDecision]
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decisions"] = [decision.to_dict() for decision in self.decisions]
        return payload


class BaseFilter:
    filter_type = "base"
    proxy_used = False
    external_dependency = ""
    external_dependency_available = False
    implemented_but_not_run = False
    historical_baseline = False
    official_reproduction = False

    def __init__(self, config: FilterConfig) -> None:
        self.config = config
        self._last_records: list[FilterInput] = []
        self._last_result: FilterResult | None = None
        self._last_runtime_seconds = 0.0
        self._last_manifest: dict[str, Any] | None = None

    def fit(self, records: list[FilterInput]) -> "BaseFilter":
        return self

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError

    def _result(self, records: list[FilterInput], decisions: list[FilterDecision]) -> FilterResult:
        kept_ids = {decision.doc_id for decision in decisions if decision.keep}
        input_tokens = sum(record.estimated_tokens for record in records)
        kept_tokens = sum(record.estimated_tokens for record in records if record.doc_id in kept_ids)
        summary = {
            "proxy_used": self.proxy_used,
            "external_dependency": self.external_dependency,
            "external_dependency_available": self.external_dependency_available,
            "implemented_but_not_run": self.implemented_but_not_run,
            "historical_baseline": self.historical_baseline,
            "official_reproduction": self.official_reproduction,
            "notes": self.config.notes,
        }
        return FilterResult(
            filter_name=self.config.filter_name,
            filter_type=self.filter_type,
            input_docs=len(records),
            kept_docs=sum(1 for decision in decisions if decision.keep),
            input_estimated_tokens=input_tokens,
            kept_estimated_tokens=kept_tokens,
            document_keep_rate=compute_document_keep_rate(len(records), sum(1 for decision in decisions if decision.keep)),
            token_keep_rate=compute_token_keep_rate(input_tokens, kept_tokens),
            decisions=decisions,
            summary=summary,
        )

    def filter(self, records: list[FilterInput]) -> FilterResult:
        started = time.perf_counter()
        self.fit(records)
        decisions = [self.score(record) for record in records]
        result = self._result(records, decisions)
        self._last_records = list(records)
        self._last_result = result
        self._last_runtime_seconds = time.perf_counter() - started
        return result

    def write_outputs(self, output_dir: str | Path, root: Path | None = None) -> dict[str, Any]:
        from .io import write_filter_outputs

        if self._last_result is None:
            raise ValueError("filter() must be called before write_outputs()")
        self._last_manifest = write_filter_outputs(
            filter_instance=self,
            result=self._last_result,
            records=self._last_records,
            output_dir=Path(output_dir),
            root=root or Path.cwd(),
            runtime_seconds=self._last_runtime_seconds,
        )
        return self._last_manifest

    def write_manifest(self, manifest_path: str | Path) -> None:
        from .io import write_json

        if self._last_manifest is None:
            raise ValueError("write_outputs() must be called before write_manifest()")
        write_json(Path(manifest_path), self._last_manifest)
