from __future__ import annotations

import re
from collections import Counter

from .base import FilterInput

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
HTML_RE = re.compile(r"<[^>]+>")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d[\d -]{7,}\d)\b")


def _ratio(count: int, total: int) -> float:
    return count / max(1, total)


def build_risk_report(input_records: list[FilterInput], kept_records: list[FilterInput]) -> dict[str, object]:
    texts = [record.text for record in kept_records]
    joined = "\n".join(texts)
    chars = len(joined)
    normalized_counts = Counter(" ".join(record.text.casefold().split()) for record in kept_records)
    duplicate_hints = sum(count - 1 for count in normalized_counts.values() if count > 1)
    return {
        "url_ratio": _ratio(len(URL_RE.findall(joined)), max(1, len(texts))),
        "html_ratio": _ratio(len(HTML_RE.findall(joined)), max(1, len(texts))),
        "symbol_ratio": _ratio(sum(not char.isalnum() and not char.isspace() for char in joined), chars),
        "digit_ratio": _ratio(sum(char.isdigit() for char in joined), chars),
        "estimated_pii_hits": len(EMAIL_RE.findall(joined)) + len(PHONE_RE.findall(joined)),
        "duplicate_hint_rate": _ratio(duplicate_hints, max(1, len(input_records))),
        "notes": "Step 4 lightweight risk summary for smoke verification; not a final evaluation metric.",
    }
