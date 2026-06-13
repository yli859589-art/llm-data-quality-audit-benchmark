from __future__ import annotations

import math
import re
from statistics import mean

from .base import FilterInput

TOKEN_RE = re.compile(r"\b\w+\b")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def build_diversity_report(records: list[FilterInput]) -> dict[str, object]:
    tokens = [token for record in records for token in tokenize(record.text)]
    lengths = [len(tokenize(record.text)) for record in records]
    length_mean = mean(lengths) if lengths else 0.0
    length_std = (
        math.sqrt(sum((length - length_mean) ** 2 for length in lengths) / len(lengths))
        if lengths
        else 0.0
    )
    return {
        "unique_token_ratio": len(set(tokens)) / max(1, len(tokens)),
        "length_mean": length_mean,
        "length_std": length_std,
        "lexical_diversity": len(set(tokens)) / max(1, len(tokens)),
        "source_count": len({record.source for record in records if record.source}),
        "notes": "Step 4 lightweight diversity summary; not a final Step 7 diversity evaluation.",
    }
