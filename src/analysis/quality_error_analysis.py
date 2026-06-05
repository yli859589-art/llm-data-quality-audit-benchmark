from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

TOKEN_RE = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def safe_excerpt(text: str, limit: int = 220) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", cleaned)
    cleaned = re.sub(r"\b(?:\+?\d[\d\-\s]{7,}\d)\b", "[PHONE]", cleaned)
    return cleaned[:limit]


def entropy_from_counter(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counter.values())


def token_distribution(documents: Iterable[str], *, top_k: int | None = None) -> Counter[str]:
    counter: Counter[str] = Counter()
    for document in documents:
        counter.update(tokenize(document))
    if top_k is None:
        return counter
    return Counter(dict(counter.most_common(top_k)))


def length_distribution(documents: Iterable[str], bins: list[int] | None = None) -> Counter[str]:
    bins = bins or [0, 40, 80, 160, 320, 640, 1280, 2560, 10**9]
    counter: Counter[str] = Counter()
    for document in documents:
        length = len(tokenize(document))
        for low, high in zip(bins, bins[1:], strict=False):
            if low <= length < high:
                counter[f"{low}-{high}"] += 1
                break
    return counter


def _probability_map(counter: Counter[str], vocabulary: set[str]) -> dict[str, float]:
    smoothing = 1e-9
    total = sum(counter.values()) + smoothing * len(vocabulary)
    return {key: (counter.get(key, 0) + smoothing) / total for key in vocabulary}


def kl_divergence(left: Counter[str], right: Counter[str]) -> float:
    vocabulary = set(left) | set(right)
    if not vocabulary:
        return 0.0
    left_prob = _probability_map(left, vocabulary)
    right_prob = _probability_map(right, vocabulary)
    return sum(left_prob[key] * math.log2(left_prob[key] / right_prob[key]) for key in vocabulary)


def js_divergence(left: Counter[str], right: Counter[str]) -> float:
    vocabulary = set(left) | set(right)
    if not vocabulary:
        return 0.0
    left_prob = _probability_map(left, vocabulary)
    right_prob = _probability_map(right, vocabulary)
    middle = {key: 0.5 * (left_prob[key] + right_prob[key]) for key in vocabulary}
    left_kl = sum(left_prob[key] * math.log2(left_prob[key] / middle[key]) for key in vocabulary)
    right_kl = sum(
        right_prob[key] * math.log2(right_prob[key] / middle[key]) for key in vocabulary
    )
    return 0.5 * (left_kl + right_kl)


def document_metrics(text: str, dev_distribution: Counter[str] | None = None) -> dict[str, float]:
    tokens = tokenize(text)
    token_count = len(tokens)
    token_counter = Counter(tokens)
    bigrams = list(zip(tokens, tokens[1:], strict=False))
    trigrams = list(zip(tokens, tokens[1:], tokens[2:], strict=False))
    repetition_rate = 1.0 - len(set(bigrams)) / max(1, len(bigrams))
    trigram_repetition_rate = 1.0 - len(set(trigrams)) / max(1, len(trigrams))
    symbol_fraction = sum(not char.isalnum() and not char.isspace() for char in text) / max(
        1, len(text)
    )
    token_entropy = entropy_from_counter(token_counter)
    char_entropy = entropy_from_counter(Counter(text))
    diversity = len(token_counter) / max(1, token_count)
    dev_loss_proxy = 0.0
    if dev_distribution is not None and tokens:
        vocabulary = set(dev_distribution) | set(tokens)
        dev_prob = _probability_map(dev_distribution, vocabulary)
        dev_loss_proxy = -sum(math.log(dev_prob[token]) for token in tokens) / len(tokens)
    return {
        "length_chars": float(len(text)),
        "token_count": float(token_count),
        "token_diversity": diversity,
        "repetition_rate": repetition_rate,
        "trigram_repetition_rate": trigram_repetition_rate,
        "token_entropy": token_entropy,
        "char_entropy": char_entropy,
        "symbol_fraction": symbol_fraction,
        "dev_loss_proxy": dev_loss_proxy,
        "information_density": token_entropy * diversity,
    }


def pearson_correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=False))
    left_var = sum((x - left_mean) ** 2 for x in left)
    right_var = sum((y - right_mean) ** 2 for y in right)
    if left_var <= 0 or right_var <= 0:
        return 0.0
    return numerator / math.sqrt(left_var * right_var)
