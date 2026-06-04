from __future__ import annotations

import argparse

from experiment_utils import root

from data.dataset_manifest import write_dataset_manifest
from data.real_corpora import load_documents_from_config
from data.splitter import deterministic_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    loaded = load_documents_from_config(root / args.config, root=root)
    seed = int(loaded.metadata.get("seed", 13))
    splits = deterministic_split(loaded.documents, seed=seed)
    output_dir = (
        root / args.output_dir
        if args.output_dir
        else root / "artifacts" / "data" / loaded.dataset_key
    )
    manifest = write_dataset_manifest(
        root=root,
        dataset_key=loaded.dataset_key,
        documents=loaded.documents,
        splits=splits,
        metadata=loaded.metadata,
        output_dir=output_dir,
    )
    latest_dir = root / "artifacts"
    write_dataset_manifest(
        root=root,
        dataset_key=loaded.dataset_key,
        documents=loaded.documents,
        splits=splits,
        metadata=loaded.metadata,
        output_dir=latest_dir,
    )
    print(f"Prepared dataset: {loaded.dataset_key}")
    print(f"Documents: {manifest['document_count']}")
    print(f"Tokens: {manifest['token_count']}")
    print(f"Used fallback: {manifest['used_fallback']}")
    print(f"Manifest: {output_dir / 'data_manifest.json'}")


if __name__ == "__main__":
    main()
