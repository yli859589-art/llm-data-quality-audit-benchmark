from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\b(?:\+?\d[\d\-\s]{7,}\d)\b")
ID_RE = re.compile(r"\bID-\d{2}-\d{4}\b")
URL_HTML_RE = re.compile(r"https?://\S+|<[^>]+>")


@dataclass(frozen=True)
class QualityWeights:
    lexical_diversity: float = 1.0
    char_entropy: float = 1.0
    repetition_penalty: float = 1.3
    pii_density_penalty: float = 1.2
    url_html_noise_penalty: float = 1.0
    non_linguistic_symbol_penalty: float = 1.0
    length_prior: float = 0.8
    language_consistency: float = 0.7
    duplicate_cluster_penalty: float = 0.0


@dataclass(frozen=True)
class DocumentQuality:
    index: int
    score: float
    components: dict[str, float]


def lexical_diversity(text: str) -> float:
    words = re.findall(r"\w+", text.casefold())
    return len(set(words)) / max(1, len(words))


def char_entropy(text: str) -> float:
    counts = Counter(text)
    total = max(1, len(text))
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    return min(1.0, entropy / 5.0)


def repetition_penalty(text: str) -> float:
    words = re.findall(r"\w+", text.casefold())
    if len(words) < 2:
        return 1.0
    bigrams = list(zip(words, words[1:], strict=False))
    repeated_fraction = 1 - len(set(bigrams)) / max(1, len(bigrams))
    return max(0.0, 1 - repeated_fraction)


def pii_density_penalty(text: str) -> float:
    hits = len(EMAIL_RE.findall(text)) + len(PHONE_RE.findall(text)) + len(ID_RE.findall(text))
    return max(0.0, 1 - 10 * hits / max(1, len(text.split())))


def url_html_noise_penalty(text: str) -> float:
    hits = len(URL_HTML_RE.findall(text))
    return max(0.0, 1 - 0.35 * hits)


def non_linguistic_symbol_penalty(text: str) -> float:
    symbol_fraction = sum(not char.isalnum() and not char.isspace() for char in text) / max(
        1, len(text)
    )
    return max(0.0, 1 - 4 * symbol_fraction)


def length_prior(text: str) -> float:
    length = len(text)
    if length < 40:
        return length / 40
    if length > 1000:
        return max(0.0, 1 - (length - 1000) / 2000)
    return 1.0


def language_consistency(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    ascii_letters = sum(char.isascii() for char in letters)
    return ascii_letters / len(letters)


def score_document(
    text: str,
    weights: QualityWeights | None = None,
    *,
    duplicate_cluster_penalty: float = 1.0,
) -> tuple[float, dict[str, float]]:
    weights = weights or QualityWeights()
    components = {
        "lexical_diversity": lexical_diversity(text),
        "char_entropy": char_entropy(text),
        "repetition_penalty": repetition_penalty(text),
        "pii_density_penalty": pii_density_penalty(text),
        "url_html_noise_penalty": url_html_noise_penalty(text),
        "non_linguistic_symbol_penalty": non_linguistic_symbol_penalty(text),
        "length_prior": length_prior(text),
        "language_consistency": language_consistency(text),
        "duplicate_cluster_penalty": duplicate_cluster_penalty,
    }
    weight_map = asdict(weights)
    total_weight = sum(weight_map.values())
    score = sum(weight_map[name] * components[name] for name in weight_map) / max(
        1e-12, total_weight
    )
    return min(1.0, max(0.0, score)), components


def score_documents(
    documents: list[str], weights: QualityWeights | None = None
) -> list[DocumentQuality]:
    output = []
    for index, document in enumerate(documents):
        score, components = score_document(document, weights)
        output.append(DocumentQuality(index, score, components))
    return output


def filter_by_quality(
    documents: list[str],
    *,
    threshold: float = 0.58,
    retention_ratio: float | None = None,
    weights: QualityWeights | None = None,
) -> tuple[list[str], list[DocumentQuality]]:
    scored = score_documents(documents, weights)
    ranked = sorted(scored, key=lambda row: row.score, reverse=True)
    if retention_ratio is not None:
        if not 0 < retention_ratio <= 1:
            raise ValueError("retention_ratio must be in (0, 1].")
        selected = ranked[: max(1, math.ceil(len(ranked) * retention_ratio))]
    else:
        selected = [row for row in ranked if row.score >= threshold]
    selected_indices = {row.index for row in selected}
    return [
        document for index, document in enumerate(documents) if index in selected_indices
    ], scored
