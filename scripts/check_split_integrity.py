from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root


def _load_manifest() -> dict[str, object]:
    path = root / "artifacts" / "data" / "wikitext2_paper" / "data_manifest.json"
    if not path.exists():
        raise SystemExit("Missing WikiText-2 paper data manifest")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_docs(split: str) -> list[str]:
    path = root / "data" / "real" / "wikitext2_raw" / f"{split}.txt"
    if not path.exists():
        raise SystemExit(f"Missing official split file: {path.relative_to(root)}")
    # Match the article-level loader used by src/data/real_corpora.py.
    from data.real_corpora import _read_wikitext_articles

    return _read_wikitext_articles(path)


def _token_set(document: str) -> set[str]:
    return set(document.casefold().split())


def _jaccard(left_tokens: set[str], right_tokens: set[str]) -> float:
    return len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))


def main() -> None:
    manifest = _load_manifest()
    errors: list[str] = []
    for field in ["split_hash_train", "split_hash_dev", "split_hash_test"]:
        if not manifest.get(field):
            errors.append(f"manifest missing {field}")
    if manifest.get("dataset_scope") != "official_split":
        errors.append("WikiText-2 paper dataset_scope must be official_split")
    if not manifest.get("sample_seed"):
        errors.append("manifest missing sample_seed")
    if "scripts/prepare_real_data.py" not in str(manifest.get("generated_by_script", "")):
        errors.append("manifest missing split generation script")
    local_path = manifest.get("local_path", {})
    if not isinstance(local_path, dict) or not {"train", "dev", "test"}.issubset(local_path):
        errors.append("manifest local_path must record train/dev/test official split files")

    split_hashes = manifest.get("split_document_hashes", {})
    if not isinstance(split_hashes, dict):
        errors.append("manifest missing split_document_hashes")
        split_hashes = {}
    split_sets = {name: set(split_hashes.get(name, [])) for name in ["train", "dev", "test"]}
    for left, right in [("train", "dev"), ("train", "test"), ("dev", "test")]:
        overlap = split_sets[left] & split_sets[right]
        if overlap:
            errors.append(f"{left}/{right} exact document overlap: {len(overlap)}")

    docs = {name: _read_docs(name) for name in ["train", "dev", "test"]}
    for left, right in [("train", "dev"), ("train", "test"), ("dev", "test")]:
        left_sample = [(len(doc.split()), _token_set(doc)) for doc in docs[left][:200]]
        right_sample = [(len(doc.split()), _token_set(doc)) for doc in docs[right][:200]]
        near = [
            (index_left, index_right)
            for index_left, (left_count, left_tokens) in enumerate(left_sample)
            for index_right, (right_count, right_tokens) in enumerate(right_sample)
            if left_count > 40
            and right_count > 40
            and _jaccard(left_tokens, right_tokens) >= 0.98
        ]
        if near:
            errors.append(f"{left}/{right} high-similarity near duplicate sample hits: {near[:3]}")

    report = {
        "status": "failed" if errors else "passed",
        "errors": errors,
        "dataset_scope": manifest.get("dataset_scope"),
        "official_split_evidence": local_path,
        "checked_by": "scripts/check_split_integrity.py",
    }
    output = root / "artifacts" / "data" / "wikitext2_paper" / "split_integrity_report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Split integrity check failed." + "\n" + "\n".join(errors))
    print("Split integrity check: ok")


if __name__ == "__main__":
    main()
