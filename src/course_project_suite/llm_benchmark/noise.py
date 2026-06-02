from __future__ import annotations

from dataclasses import asdict, dataclass
import random


@dataclass(frozen=True)
class NoiseConfig:
    seed: int = 17
    html_boilerplate: bool = True
    url_spam: bool = True
    pii_canaries: bool = True
    exact_duplicates: bool = True
    near_duplicates: bool = True
    ocr_corruption: bool = True
    mojibake: bool = True
    repeated_ngrams: bool = True
    low_information_templates: bool = True
    mixed_language: bool = True
    excessive_symbols: bool = True
    generated_repetition: bool = True


@dataclass(frozen=True)
class NoiseResult:
    documents: list[str]
    report: dict[str, object]


def _increment(counts: dict[str, int], name: str) -> None:
    counts[name] = counts.get(name, 0) + 1


def inject_controlled_noise(
    documents: list[str], config: NoiseConfig = NoiseConfig()
) -> NoiseResult:
    """Inject deterministic stress-test noise with independently toggled families."""
    rng = random.Random(config.seed)
    output: list[str] = []
    counts: dict[str, int] = {}
    canaries: list[dict[str, str]] = []

    for index, document in enumerate(documents):
        value = document
        if config.html_boilerplate and index % 3 == 0:
            value = f"<article><nav>archive</nav>{value}</article>"
            _increment(counts, "html_boilerplate")
        if config.url_spam and index % 4 == 0:
            value += f" https://spam.example.invalid/archive/{index}?ref=promo"
            _increment(counts, "url_spam")
        if config.pii_canaries and index % 7 == 0:
            email = f"editor{index}@example.org"
            phone = f"+1 412 555 {1000 + index:04d}"
            identifier = f"ID-{config.seed:02d}-{index:04d}"
            value += f" Contact {email} or {phone}; reference {identifier}."
            canaries.append({"email": email, "phone": phone, "id_like": identifier})
            _increment(counts, "pii_canaries")
        if config.ocr_corruption and index % 9 == 0:
            value = value.replace("the", "tbe", 1).replace("ing", "1ng", 1)
            _increment(counts, "ocr_corruption")
        if config.mojibake and index % 10 == 0:
            value += " Encoding sample: cafÃ© â€™ â€œ."
            _increment(counts, "mojibake")
        if config.repeated_ngrams and index % 11 == 0:
            value += " repeated phrase repeated phrase repeated phrase"
            _increment(counts, "repeated_ngrams")
        if config.mixed_language and index % 13 == 0:
            value += " mixed language snippet bonjour mundo"
            _increment(counts, "mixed_language")
        if config.excessive_symbols and index % 6 == 0:
            value += " !!! ### $$$ %%%"
            _increment(counts, "excessive_symbols")

        output.append(value)
        if config.exact_duplicates and index % 5 == 0:
            output.append(value)
            _increment(counts, "exact_duplicates")
        if config.near_duplicates and index % 8 == 0:
            output.append(value + " updated")
            _increment(counts, "near_duplicates")

        if config.low_information_templates and index % 8 == 0:
            output.append(("template navigation footer " * (8 + index % 3)).strip())
            _increment(counts, "low_information_templates")
        if config.generated_repetition and index % 12 == 0:
            output.append(("generated continuation loop " * (10 + index % 4)).strip())
            _increment(counts, "generated_repetition")

    rng.shuffle(output)
    report: dict[str, object] = {
        "seed": config.seed,
        "configuration": asdict(config),
        "input_documents": len(documents),
        "output_documents": len(output),
        "injected_counts": counts,
        "synthetic_pii_canaries": canaries,
        "note": (
            "Counts describe deterministic synthetic stress-test interventions. "
            "They do not estimate naturally occurring web-corpus noise."
        ),
    }
    return NoiseResult(output, report)
