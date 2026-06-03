from __future__ import annotations

import random
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NoiseConfig:
    seed: int = 17
    intensity: float = 1.0
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
    navigation_bars: bool = True
    footer_copyright: bool = True
    seo_keyword_stuffing: bool = True
    ad_blocks: bool = True
    cookie_banners: bool = True
    malformed_html: bool = True
    boilerplate_templates: bool = True
    multilingual_fragments: bool = True
    encoding_artifacts: bool = True
    low_information_pages: bool = True
    repeated_template_pages: bool = True


@dataclass(frozen=True)
class NoiseResult:
    documents: list[str]
    report: dict[str, object]


def _increment(counts: dict[str, int], name: str) -> None:
    counts[name] = counts.get(name, 0) + 1


def inject_controlled_noise(documents: list[str], config: NoiseConfig | None = None) -> NoiseResult:
    """Inject deterministic stress-test noise with independently toggled families."""
    config = config or NoiseConfig()
    if config.intensity <= 0:
        return NoiseResult(
            list(documents),
            {
                "seed": config.seed,
                "configuration": asdict(config),
                "input_documents": len(documents),
                "output_documents": len(documents),
                "injected_counts": {},
                "synthetic_pii_canaries": [],
                "note": "Noise disabled because intensity <= 0.",
            },
        )
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
        if config.navigation_bars and index % 4 == 1:
            value = f"Home Archive About Login Search :: {value}"
            _increment(counts, "navigation_bars")
        if config.footer_copyright and index % 5 == 2:
            value += " Copyright 2024 Example Media. Terms Privacy Contact."
            _increment(counts, "footer_copyright")
        if config.seo_keyword_stuffing and index % 6 == 2:
            value += " AI benchmark data quality language model best guide tutorial"
            _increment(counts, "seo_keyword_stuffing")
        if config.ad_blocks and index % 7 == 3:
            value += " Sponsored: buy cloud credits now now now."
            _increment(counts, "ad_blocks")
        if config.cookie_banners and index % 8 == 3:
            value += " Cookie settings accept reject manage preferences."
            _increment(counts, "cookie_banners")
        if config.malformed_html and index % 9 == 4:
            value += " <div><span><p>broken markup"
            _increment(counts, "malformed_html")
        if config.boilerplate_templates and index % 10 == 4:
            value += " template header sidebar footer template header sidebar footer"
            _increment(counts, "boilerplate_templates")
        if config.multilingual_fragments and index % 11 == 5:
            value += " hola mundo bonjour données modelo texto"
            _increment(counts, "multilingual_fragments")
        if config.encoding_artifacts and index % 12 == 5:
            value += " mojibake sample: Ã© â€™ �"
            _increment(counts, "encoding_artifacts")

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
        if config.low_information_pages and index % 14 == 0:
            output.append(("login signup settings profile " * 12).strip())
            _increment(counts, "low_information_pages")
        if config.repeated_template_pages and index % 15 == 0:
            output.append(("article card related links " * 14).strip())
            _increment(counts, "repeated_template_pages")

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
