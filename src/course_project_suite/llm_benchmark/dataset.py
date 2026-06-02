from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import random
import re
from urllib.request import urlopen

from course_project_suite.cs336.data import clean_common_crawl_text, quality_filter, redact_pii

DATASET_URL = 'https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt'
DATASET_SHA256 = '86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed'
EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
PHONE_RE = re.compile(r'\b(?:\+?\d[\d\-\s]{7,}\d)\b')


@dataclass(frozen=True)
class CorpusSource:
    path: str
    url: str
    sha256: str
    chars: int


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_public_corpus(path: str | Path, allow_download: bool = False) -> tuple[str, CorpusSource]:
    path = Path(path)
    if not path.exists():
        if not allow_download:
            raise FileNotFoundError(f'Missing public corpus: {path}. Run scripts/fetch_public_data.py first.')
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(DATASET_URL, timeout=60) as response:
            path.write_bytes(response.read())
    text = path.read_text(encoding='utf-8')
    digest = sha256_text(text)
    if digest != DATASET_SHA256:
        raise ValueError(f'Unexpected Tiny Shakespeare SHA-256: {digest}')
    return text, CorpusSource(str(path), DATASET_URL, digest, len(text))


def chunk_documents(text: str, chunk_chars: int = 360, max_documents: int = 160) -> list[str]:
    text = re.sub(r'\r\n?', '\n', text)
    chunks = []
    for start in range(0, len(text), chunk_chars):
        chunk = text[start:start + chunk_chars].strip()
        if chunk:
            chunks.append(chunk)
        if len(chunks) >= max_documents:
            break
    return chunks


def inject_web_noise(documents: list[str], seed: int = 17) -> list[str]:
    rng = random.Random(seed)
    noisy = []
    for index, document in enumerate(documents):
        value = document
        if index % 3 == 0:
            value = f'<article>{value}</article> https://example.org/archive/{index}'
        if index % 7 == 0:
            value += f' Contact editor{index}@example.org or +1 412 555 {1000 + index:04d}.'
        if index % 11 == 0:
            value += ' !!! ### $$$ %%%'
        noisy.append(value)
        if index % 5 == 0:
            noisy.append(value)
        noisy.append((f'@@@@ #### $$$$ !!!! **** {index} ' * (9 + index % 4)).strip())
    noisy.extend([
        '@@@@ #### $$$$ !!!! **** ' * 18,
        '<div>https://spam.example.invalid</div> $$$ !!! ### ' * 12,
    ])
    rng.shuffle(noisy)
    return noisy


def exact_deduplicate_stable(documents: list[str]) -> list[str]:
    seen = set()
    output = []
    for document in documents:
        digest = hashlib.sha1(document.encode('utf-8')).hexdigest()
        if digest not in seen:
            seen.add(digest)
            output.append(document)
    return output


def apply_pipeline(
    documents: list[str],
    *,
    clean: bool,
    redact: bool,
    deduplicate: bool,
    filter_quality: bool,
) -> list[str]:
    output = list(documents)
    if clean:
        output = [clean_common_crawl_text(document) for document in output]
    if redact:
        output = [redact_pii(document) for document in output]
    if filter_quality:
        output = [document for document in output if quality_filter(document)]
    if deduplicate:
        output = exact_deduplicate_stable(output)
    return output


def build_ablation_variants(documents: list[str]) -> dict[str, list[str]]:
    settings = {
        'raw_noisy_baseline': {},
        'clean_redact': {'clean': True, 'redact': True},
        'deduplicate_only': {'deduplicate': True},
        'quality_filter_only': {'filter_quality': True},
        'full_pipeline': {'clean': True, 'redact': True, 'deduplicate': True, 'filter_quality': True},
    }
    defaults = {'clean': False, 'redact': False, 'deduplicate': False, 'filter_quality': False}
    return {name: apply_pipeline(documents, **(defaults | overrides)) for name, overrides in settings.items()}


def quality_metrics(documents: list[str]) -> dict[str, float | int]:
    counts = Counter(documents)
    duplicate_documents = sum(count - 1 for count in counts.values() if count > 1)
    chars = sum(len(document) for document in documents)
    return {
        'documents': len(documents),
        'characters': chars,
        'duplicate_documents': duplicate_documents,
        'duplicate_rate': duplicate_documents / max(1, len(documents)),
        'email_hits': sum(len(EMAIL_RE.findall(document)) for document in documents),
        'phone_hits': sum(len(PHONE_RE.findall(document)) for document in documents),
        'quality_pass_rate': sum(quality_filter(document) for document in documents) / max(1, len(documents)),
    }


def concatenate_documents(documents: list[str], limit_chars: int | None = None) -> str:
    text = '\n\n'.join(documents)
    return text if limit_chars is None else text[:limit_chars]


def analyze_removed_documents(raw_documents: list[str], cleaned_documents: list[str]) -> dict[str, object]:
    cleaned = set(cleaned_documents)
    sanitized_examples = []
    for document in raw_documents:
        normalized = redact_pii(clean_common_crawl_text(document))
        if normalized not in cleaned and len(sanitized_examples) < 3:
            sanitized_examples.append(normalized[:180])
    return {
        'removed_documents': len(raw_documents) - len(cleaned_documents),
        'sanitized_removed_examples': sanitized_examples,
        'note': 'Examples are redacted before reporting and may include duplicates or quality-filter failures.',
    }
