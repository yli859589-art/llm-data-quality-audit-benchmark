from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from course_project_suite.llm_benchmark.dedup import exact_deduplicate
from course_project_suite.llm_benchmark.quality import (
    EMAIL_RE,
    ID_RE,
    PHONE_RE,
    filter_by_quality,
)
from data.token_counting import count_tokens
from filters.hdqspp_v2 import select_hdqspp_v2
from filters.hdqspp_v3 import select_hdqspp_v3

URL_HTML_RE = re.compile(r"https?://\S+|<[^>]+>")


@dataclass(frozen=True)
class BaselineResult:
    name: str
    input_documents: int
    output_documents: int
    retention_rate: float
    input_tokens: int
    output_tokens: int
    pii_hits_before: int
    pii_hits_after: int
    removed_duplicates: int = 0
    skipped: bool = False
    skip_reason: str = ""
    notes: str = ""


def _pii_hits(documents: list[str]) -> int:
    text = "\n".join(documents)
    return len(EMAIL_RE.findall(text)) + len(PHONE_RE.findall(text)) + len(ID_RE.findall(text))


def _result(
    name: str,
    input_documents: list[str],
    output_documents: list[str],
    *,
    removed_duplicates: int = 0,
    skipped: bool = False,
    skip_reason: str = "",
    notes: str = "",
) -> BaselineResult:
    return BaselineResult(
        name=name,
        input_documents=len(input_documents),
        output_documents=len(output_documents),
        retention_rate=len(output_documents) / max(1, len(input_documents)),
        input_tokens=sum(count_tokens(document) for document in input_documents),
        output_tokens=sum(count_tokens(document) for document in output_documents),
        pii_hits_before=_pii_hits(input_documents),
        pii_hits_after=_pii_hits(output_documents),
        removed_duplicates=removed_duplicates,
        skipped=skipped,
        skip_reason=skip_reason,
        notes=notes,
    )


def _keep_count(total: int, target_keep_rate: float | None) -> int:
    if target_keep_rate is None:
        return total
    if not 0 < target_keep_rate <= 1:
        raise ValueError("target_keep_rate must be in (0, 1]")
    return max(1, math.ceil(total * target_keep_rate))


def _random_same_keep_rate(documents: list[str], target_keep_rate: float, seed: int) -> list[str]:
    indexed = list(enumerate(documents))
    random.Random(seed).shuffle(indexed)
    keep_indices = {index for index, _ in indexed[: _keep_count(len(documents), target_keep_rate)]}
    return [document for index, document in enumerate(documents) if index in keep_indices]


def _length_filter(documents: list[str], target_keep_rate: float | None) -> list[str]:
    ranked = sorted(enumerate(documents), key=lambda row: len(row[1]), reverse=True)
    keep_indices = {index for index, _ in ranked[: _keep_count(len(documents), target_keep_rate)]}
    return [document for index, document in enumerate(documents) if index in keep_indices]


def _heuristic_quality(text: str) -> float:
    words = re.findall(r"\w+", text)
    alpha_chars = sum(char.isalpha() for char in text)
    symbol_chars = sum(not char.isalnum() and not char.isspace() for char in text)
    length_score = min(1.0, len(words) / 80)
    language_score = alpha_chars / max(1, len(text))
    symbol_score = max(0.0, 1 - 4 * symbol_chars / max(1, len(text)))
    url_score = max(0.0, 1 - 0.4 * len(URL_HTML_RE.findall(text)))
    return 0.3 * length_score + 0.3 * language_score + 0.2 * symbol_score + 0.2 * url_score


def _ranked_keep(
    documents: list[str],
    scores: list[float],
    target_keep_rate: float | None,
) -> list[str]:
    ranked = sorted(enumerate(scores), key=lambda row: row[1], reverse=True)
    keep_indices = {index for index, _ in ranked[: _keep_count(len(documents), target_keep_rate)]}
    return [document for index, document in enumerate(documents) if index in keep_indices]


def _ngram_proxy_score(text: str) -> float:
    tokens = re.findall(r"\w+", text.casefold())
    if not tokens:
        return 0.0
    counts = Counter(zip(tokens, tokens[1:], strict=False))
    repetition = 1 - len(counts) / max(1, len(tokens) - 1)
    lexical = len(set(tokens)) / len(tokens)
    return max(0.0, min(1.0, 0.65 * lexical + 0.35 * (1 - repetition)))


def _independent_quality_score(text: str) -> float:
    words = re.findall(r"\w+", text.casefold())
    if not words:
        return 0.0
    unique = len(set(words)) / len(words)
    length = min(1.0, len(words) / 120)
    symbol_penalty = sum(not char.isalnum() and not char.isspace() for char in text)
    symbol_score = max(0.0, 1 - 3 * symbol_penalty / max(1, len(text)))
    return 0.45 * unique + 0.35 * length + 0.20 * symbol_score


def run_baseline(
    name: str,
    documents: list[str],
    *,
    target_keep_rate: float | None = None,
    seed: int = 13,
) -> tuple[list[str], BaselineResult]:
    if name == "raw":
        output = list(documents)
        return output, _result(name, documents, output, notes="No filtering baseline.")
    if name == "random_same_keep_rate":
        if target_keep_rate is None:
            raise ValueError("random_same_keep_rate requires target_keep_rate")
        output = _random_same_keep_rate(documents, target_keep_rate, seed)
        return output, _result(name, documents, output, notes="Seeded random retention.")
    if name == "length_filter":
        output = _length_filter(documents, target_keep_rate)
        return output, _result(name, documents, output, notes="Keeps longest documents.")
    if name == "c4_gopher_heuristic":
        scores = [_heuristic_quality(document) for document in documents]
        output = _ranked_keep(documents, scores, target_keep_rate)
        return output, _result(name, documents, output, notes="Small C4/Gopher-style proxy.")
    if name == "dedup_only":
        deduped = exact_deduplicate(documents)
        return deduped.documents, _result(
            name,
            documents,
            deduped.documents,
            removed_duplicates=deduped.removed,
            notes="Exact duplicate removal only.",
        )
    if name == "perplexity_quality_ngram":
        scores = [_ngram_proxy_score(document) for document in documents]
        output = _ranked_keep(documents, scores, target_keep_rate)
        return output, _result(
            name,
            documents,
            output,
            notes="N-gram repetition/lexical proxy; not a neural LM perplexity score.",
        )
    if name == "independent_quality_score":
        scores = [_independent_quality_score(document) for document in documents]
        output = _ranked_keep(documents, scores, target_keep_rate)
        return output, _result(
            name,
            documents,
            output,
            notes="Independent lexical/length/symbol score, separate from HDQS++ weights.",
        )
    if name == "hdqspp":
        output, _ = filter_by_quality(documents, retention_ratio=target_keep_rate)
        return output, _result(
            name,
            documents,
            output,
            notes="HDQS++ filtering baseline; training handled by run_experiment.py.",
        )
    if name == "hdqspp_v2":
        output, _ = select_hdqspp_v2(
            documents,
            reference_documents=documents,
        )
        return output, _result(
            name,
            documents,
            output,
            notes="HDQS++ v2 filtering with distribution-preserving selection.",
        )
    if name == "hdqspp_v2_no_token_frequency":
        output, _ = select_hdqspp_v2(
            documents,
            reference_documents=documents,
            variant="v2_without_token_frequency_preservation",
        )
        return output, _result(
            name,
            documents,
            output,
            notes="HDQS++ v2 diagnostic variant with token-frequency preservation removed.",
        )
    if name == "hdqspp_v3":
        output, _ = select_hdqspp_v3(
            documents,
            reference_documents=documents,
            variant="hdqspp_v3",
            seed=seed,
        )
        return output, _result(
            name,
            documents,
            output,
            notes="HDQS++ v3 calibrated soft-selection filtering candidate.",
        )
    if name == "optional_external_wrapper":
        empty_result = _result(
            name,
            documents,
            [],
            skipped=True,
            skip_reason="No external wrapper command configured.",
        )
        return [], empty_result
    raise ValueError(f"Unknown baseline: {name}")


def write_baseline_artifacts(
    *,
    output_dir: Path,
    baseline_name: str,
    documents: list[str],
    result: BaselineResult,
) -> dict[str, Any]:
    baseline_dir = output_dir / baseline_name
    baseline_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = baseline_dir / "metrics.json"
    sample_path = baseline_dir / "retained_sample.txt"
    metrics = asdict(result)
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    sample_path.write_text("\n\n".join(documents[:5]), encoding="utf-8")
    return {"metrics": metrics_path.as_posix(), "sample": sample_path.as_posix()}


def run_baseline_suite(
    documents: list[str],
    baseline_names: list[str],
    *,
    target_keep_rate: float | None = None,
    seed: int = 13,
) -> list[tuple[list[str], BaselineResult]]:
    return [
        run_baseline(name, documents, target_keep_rate=target_keep_rate, seed=seed)
        for name in baseline_names
    ]
