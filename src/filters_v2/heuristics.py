from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"\b\w+\b")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
HTML_RE = re.compile(r"<[^>]+>")


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def token_set(text: str) -> set[str]:
    return set(tokens(text))


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / max(1, len(left | right))


def symbol_ratio(text: str) -> float:
    return sum(not char.isalnum() and not char.isspace() for char in text) / max(1, len(text))


def punctuation_ratio(text: str) -> float:
    return sum(char in ".,;:!?\"'()[]{}" for char in text) / max(1, len(text))


def repeated_line_ratio(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    counts = Counter(lines)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / len(lines)


def unique_word_ratio(text: str) -> float:
    toks = tokens(text)
    return len(set(toks)) / max(1, len(toks))


def stopword_ratio(text: str) -> float:
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "is",
        "for",
        "with",
        "that",
        "this",
        "it",
    }
    toks = tokens(text)
    return sum(token in stopwords for token in toks) / max(1, len(toks))


def language_text_ratio(text: str) -> float:
    return sum(char.isalpha() or char.isspace() for char in text) / max(1, len(text))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def unigram_surprisal_scores(texts: list[str]) -> list[float]:
    corpus = Counter(token for text in texts for token in tokens(text))
    total = sum(corpus.values()) + max(1, len(corpus))
    scores: list[float] = []
    for text in texts:
        toks = tokens(text)
        if not toks:
            scores.append(0.0)
            continue
        surprisal = 0.0
        for token in toks:
            prob = (corpus[token] + 1) / total
            surprisal += -math.log(prob)
        mean_surprisal = surprisal / len(toks)
        scores.append(1.0 / (1.0 + mean_surprisal))
    return scores
