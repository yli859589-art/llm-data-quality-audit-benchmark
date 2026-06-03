from __future__ import annotations

import hashlib
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from urllib.request import urlopen

from course_project_suite.cs336.data import (
    clean_common_crawl_text,
    quality_filter,
    redact_pii,
)

from .dedup import exact_deduplicate, near_deduplicate
from .near_dedup import near_deduplicate as near_deduplicate_with_method
from .noise import NoiseConfig, inject_controlled_noise
from .quality import EMAIL_RE, ID_RE, PHONE_RE, filter_by_quality, score_documents

DATASET_URL = (
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
)
DATASET_SHA256 = "86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed"


@dataclass(frozen=True)
class CorpusSource:
    dataset_name: str
    path: str
    source: str
    url: str
    sha256: str
    chars: int
    license_or_usage_note: str
    split: str = "train"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def load_public_corpus(path: str | Path, allow_download: bool = False) -> tuple[str, CorpusSource]:
    path = Path(path)
    if not path.exists():
        if not allow_download:
            raise FileNotFoundError(
                f"Missing public corpus: {path}. Run scripts/fetch_public_data.py first."
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(DATASET_URL, timeout=60) as response:
            path.write_bytes(response.read())
    text = path.read_text(encoding="utf-8")
    digest = sha256_text(text)
    if digest != DATASET_SHA256:
        raise ValueError(f"Unexpected Tiny Shakespeare SHA-256: {digest}")
    return text, CorpusSource(
        dataset_name="tiny_shakespeare",
        path=_portable_path(path),
        source="karpathy/char-rnn Tiny Shakespeare mirror",
        url=DATASET_URL,
        sha256=digest,
        chars=len(text),
        license_or_usage_note=(
            "Public-domain Shakespeare-derived text mirror. See data/tinyshakespeare/SOURCE.md."
        ),
    )


def chunk_documents(text: str, chunk_chars: int = 360, max_documents: int = 160) -> list[str]:
    text = re.sub(r"\r\n?", "\n", text)
    chunks = []
    for start in range(0, len(text), chunk_chars):
        chunk = text[start : start + chunk_chars].strip()
        if chunk:
            chunks.append(chunk)
        if len(chunks) >= max_documents:
            break
    return chunks


def inject_web_noise(documents: list[str], seed: int = 17) -> list[str]:
    """Compatibility wrapper for the earlier public API."""
    return inject_controlled_noise(documents, NoiseConfig(seed=seed)).documents


def exact_deduplicate_stable(documents: list[str]) -> list[str]:
    return exact_deduplicate(documents).documents


def simple_rule_quality_filter(document: str) -> bool:
    words = re.findall(r"\w+", document.casefold())
    lexical_ratio = len(set(words)) / max(1, len(words))
    return quality_filter(document) and lexical_ratio >= 0.16


def apply_pipeline(
    documents: list[str],
    *,
    clean: bool = False,
    redact: bool = False,
    exact_dedup: bool = False,
    near_dedup: bool = False,
    rule_filter: bool = False,
    hdqs_filter: bool = False,
    quality_threshold: float = 0.80,
    near_threshold: float = 0.82,
) -> list[str]:
    output = list(documents)
    if clean:
        output = [clean_common_crawl_text(document) for document in output]
    if redact:
        output = [redact_pii(document) for document in output]
        output = [ID_RE.sub("<ID>", document) for document in output]
    if rule_filter:
        output = [document for document in output if simple_rule_quality_filter(document)]
    if hdqs_filter:
        output, _ = filter_by_quality(output, threshold=quality_threshold)
    if exact_dedup:
        output = exact_deduplicate(output).documents
    if near_dedup:
        output = near_deduplicate(output, threshold=near_threshold).documents
    return output


def build_ablation_variants(
    documents: list[str],
    *,
    quality_threshold: float = 0.80,
    near_threshold: float = 0.82,
) -> dict[str, list[str]]:
    full_pipeline = apply_pipeline(
        documents,
        clean=True,
        redact=True,
        exact_dedup=True,
        near_dedup=True,
        hdqs_filter=True,
        quality_threshold=quality_threshold,
        near_threshold=near_threshold,
    )
    full_retention = len(full_pipeline) / max(1, len(documents))
    exact_docs = exact_deduplicate(documents).documents
    jaccard_docs = near_deduplicate(documents, threshold=near_threshold).documents
    minhash_docs = near_deduplicate_with_method(
        documents, method="minhash_lsh", threshold=near_threshold
    ).documents
    quality_ranked, _ = filter_by_quality(documents, retention_ratio=full_retention)
    length_ranked = sorted(documents, key=len, reverse=True)[: max(1, len(full_pipeline))]
    random_retention = documents[: max(1, len(full_pipeline))]
    settings: dict[str, dict[str, bool | float]] = {
        "raw_noisy_baseline": {},
        "clean_only": {"clean": True},
        "pii_redact_only": {"redact": True},
        "exact_dedup_only": {"exact_dedup": True},
        "near_dedup_only": {"near_dedup": True},
        "jaccard_near_dedup_only": {"near_dedup": True},
        "rule_filter_only": {"rule_filter": True},
        "rule_quality_filter": {"rule_filter": True},
        "perplexity_filter_proxy": {
            "hdqs_filter": True,
            "quality_threshold": quality_threshold + 0.04,
        },
        "proxy_perplexity_filter": {
            "hdqs_filter": True,
            "quality_threshold": quality_threshold + 0.04,
        },
        "hdqs_filter": {"hdqs_filter": True},
        "hdqs_curriculum": {"hdqs_filter": True},
        "full_pipeline_without_clean": {
            "redact": True,
            "exact_dedup": True,
            "near_dedup": True,
            "hdqs_filter": True,
        },
        "full_pipeline_without_redact": {
            "clean": True,
            "exact_dedup": True,
            "near_dedup": True,
            "hdqs_filter": True,
        },
        "full_pipeline_without_exact_dedup": {
            "clean": True,
            "redact": True,
            "near_dedup": True,
            "hdqs_filter": True,
        },
        "full_pipeline_without_near_dedup": {
            "clean": True,
            "redact": True,
            "exact_dedup": True,
            "hdqs_filter": True,
        },
        "full_without_hdqs": {
            "clean": True,
            "redact": True,
            "exact_dedup": True,
            "near_dedup": True,
            "rule_filter": True,
        },
        "full_pipeline": {
            "clean": True,
            "redact": True,
            "exact_dedup": True,
            "near_dedup": True,
            "hdqs_filter": True,
        },
    }
    defaults = {
        "quality_threshold": quality_threshold,
        "near_threshold": near_threshold,
    }
    variants = {
        name: apply_pipeline(documents, **cast(Any, defaults | overrides))
        for name, overrides in settings.items()
    }
    variants["full_pipeline"] = full_pipeline
    variants["full_pipeline_without_hdqs"] = variants["full_without_hdqs"]
    variants["minhash_lsh_near_dedup_only"] = minhash_docs
    variants["random_retention_matched_baseline"] = random_retention
    variants["length_matched_baseline"] = length_ranked
    variants["quality_retention_matched_baseline"] = quality_ranked
    variants["exact_dedup_only"] = exact_docs
    variants["jaccard_near_dedup_only"] = jaccard_docs
    return variants


def quality_metrics(documents: list[str]) -> dict[str, float | int]:
    counts = Counter(documents)
    duplicate_documents = sum(count - 1 for count in counts.values() if count > 1)
    chars = sum(len(document) for document in documents)
    scores = score_documents(documents)
    return {
        "documents": len(documents),
        "characters": chars,
        "duplicate_documents": duplicate_documents,
        "duplicate_rate": duplicate_documents / max(1, len(documents)),
        "email_hits": sum(len(EMAIL_RE.findall(document)) for document in documents),
        "phone_hits": sum(len(PHONE_RE.findall(document)) for document in documents),
        "id_like_hits": sum(len(ID_RE.findall(document)) for document in documents),
        "quality_pass_rate": sum(simple_rule_quality_filter(document) for document in documents)
        / max(1, len(documents)),
        "mean_hdqs": sum(score.score for score in scores) / max(1, len(scores)),
    }


def concatenate_documents(documents: list[str], limit_chars: int | None = None) -> str:
    text = "\n\n".join(documents)
    return text if limit_chars is None else text[:limit_chars]


def enforce_equal_character_budget(
    variants: dict[str, list[str]], requested_chars: int
) -> tuple[dict[str, str], dict[str, object]]:
    concatenated = {name: concatenate_documents(documents) for name, documents in variants.items()}
    shared_budget = min(requested_chars, *(len(text) for text in concatenated.values()))
    trimmed = {name: text[:shared_budget] for name, text in concatenated.items()}
    report = {
        "equal_budget_enabled": True,
        "requested_characters": requested_chars,
        "shared_character_budget": shared_budget,
        "variants": {
            name: {
                "available_characters": len(concatenated[name]),
                "training_characters": len(trimmed[name]),
            }
            for name in trimmed
        },
        "note": "All compared model variants are trimmed to the same character budget.",
    }
    return trimmed, report


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        git_dir = Path(".git")
        head = git_dir / "HEAD"
        if not head.exists():
            return None
        value = head.read_text(encoding="utf-8").strip()
        if value.startswith("ref: "):
            reference = git_dir / value.removeprefix("ref: ")
            return reference.read_text(encoding="utf-8").strip() if reference.exists() else None
        return value


def build_dataset_card(
    source: CorpusSource,
    *,
    raw_documents: list[str],
    retained_documents: list[str],
    random_seed: int,
    exact_removed: int,
    near_removed: int,
) -> dict[str, object]:
    before = quality_metrics(raw_documents)
    after = quality_metrics(retained_documents)
    return {
        "dataset_name": source.dataset_name,
        "source": source.source,
        "license_or_usage_note": source.license_or_usage_note,
        "split": source.split,
        "raw_chars": before["characters"],
        "retained_chars": after["characters"],
        "retention_rate": after["characters"] / max(1, before["characters"]),
        "num_docs": len(raw_documents),
        "num_duplicates_removed": exact_removed,
        "num_near_duplicates_removed": near_removed,
        "pii_count_before": before["email_hits"] + before["phone_hits"] + before["id_like_hits"],
        "pii_count_after": after["email_hits"] + after["phone_hits"] + after["id_like_hits"],
        "random_seed": random_seed,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "code_version/git_commit": _git_commit(),
        "corpus_path": source.path,
        "sha256": source.sha256,
    }


def analyze_removed_documents(
    raw_documents: list[str], cleaned_documents: list[str]
) -> dict[str, object]:
    cleaned = set(cleaned_documents)
    sanitized_examples: list[str] = []
    for document in raw_documents:
        normalized = redact_pii(clean_common_crawl_text(document))
        normalized = ID_RE.sub("<ID>", normalized)
        if normalized not in cleaned and len(sanitized_examples) < 3:
            sanitized_examples.append(normalized[:180])
    return {
        "removed_documents": len(raw_documents) - len(cleaned_documents),
        "sanitized_removed_examples": sanitized_examples,
        "note": "Examples are redacted before reporting and may include multiple removal causes.",
    }
