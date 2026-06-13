from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path
from typing import Callable

from data_sources.base import DatasetSource, DatasetSourceConfig, OptionalDatasetUnavailable
from data_sources.load_c4 import build_source as build_c4
from data_sources.load_dolma import build_source as build_dolma
from data_sources.load_fineweb import build_source as build_fineweb
from data_sources.load_openwebtext import build_source as build_openwebtext
from data_sources.load_pile import build_source as build_pile
from data_sources.load_wikitext2 import build_source as build_wikitext2
from experiment_utils import root

BuildSource = Callable[[DatasetSourceConfig, Path | None], DatasetSource]

BUILDERS: dict[str, BuildSource] = {
    "wikitext2": build_wikitext2,
    "openwebtext": build_openwebtext,
    "c4": build_c4,
    "fineweb": build_fineweb,
    "dolma": build_dolma,
    "pile": build_pile,
}

DATASET_METADATA = {
    "wikitext2": {
        "dataset_name": "WikiText-2",
        "dataset_version": "wikitext-2-raw-v1",
        "license_note": "WikiText-2 terms apply; verify upstream license before redistribution.",
        "upstream_url_or_id": "Salesforce/wikitext",
    },
    "openwebtext": {
        "dataset_name": "OpenWebText",
        "dataset_version": "streaming-sample-protocol",
        "license_note": "OpenWebText upstream terms apply; current rows are bounded streaming-sample audit evidence.",
        "upstream_url_or_id": "openwebtext",
    },
    "c4": {
        "dataset_name": "C4 English",
        "dataset_version": "streaming-sample-protocol",
        "license_note": "C4 upstream terms apply; current rows are streaming-sample audit evidence unless full data is prepared.",
        "upstream_url_or_id": "allenai/c4",
    },
    "fineweb": {
        "dataset_name": "FineWeb",
        "dataset_version": "step2-protocol",
        "license_note": "FineWeb protocol only in Step 2 unless local cache is provided; verify upstream terms.",
        "upstream_url_or_id": "HuggingFaceFW/fineweb",
    },
    "dolma": {
        "dataset_name": "Dolma",
        "dataset_version": "step2-protocol",
        "license_note": "Dolma optional_remote protocol only in Step 2 unless local cache is provided.",
        "upstream_url_or_id": "allenai/dolma",
    },
    "pile": {
        "dataset_name": "Pile subset",
        "dataset_version": "step2-protocol",
        "license_note": "Pile subset optional protocol only in Step 2 unless local cache is provided.",
        "upstream_url_or_id": "EleutherAI/pile",
    },
}


def _source_kind(dataset: str, scope: str, cache_dir: str, allow_fallback: bool) -> str:
    if scope == "smoke":
        return "fixture"
    if dataset in {"fineweb", "dolma", "pile"} and scope == "implemented_but_not_run":
        return "optional_remote"
    if cache_dir:
        return "local"
    if dataset in {"openwebtext", "c4"}:
        return "local"
    if dataset == "wikitext2":
        return "local"
    return "optional_remote" if allow_fallback else "hf_streaming"


def _make_config(args: argparse.Namespace) -> DatasetSourceConfig:
    if args.scope in {"main", "heavy"}:
        args.allow_fallback = False
    metadata = DATASET_METADATA[args.dataset]
    source_kind = _source_kind(args.dataset, args.scope, args.cache_dir or "", args.allow_fallback)
    output = "" if args.scope == "implemented_but_not_run" else args.output
    manifest_output = args.manifest_output or str(Path(args.output).with_name("data_manifest.json"))
    return DatasetSourceConfig(
        dataset_name=str(metadata["dataset_name"]),
        dataset_version=str(metadata["dataset_version"]),
        split=args.split,
        source_kind=source_kind,
        token_budget=args.token_budget,
        sampling_seed=args.seed,
        allow_fallback=bool(args.allow_fallback),
        streaming=source_kind == "hf_streaming",
        cache_dir=args.cache_dir or "",
        output_path=output,
        manifest_path=manifest_output,
        license_note=str(metadata["license_note"]),
        scope=args.scope,
        shuffle=bool(args.shuffle),
        token_counter_type=args.token_counter_type,
        smoke_only=args.scope == "smoke",
        fallback_used=False,
        upstream_url_or_id=str(metadata["upstream_url_or_id"]),
        notes=args.notes or "",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Step 2 data-source JSONL and manifest artifacts.")
    parser.add_argument("--dataset", required=True, choices=sorted(BUILDERS))
    parser.add_argument("--split", required=True, choices=["train", "validation", "dev", "test"])
    parser.add_argument(
        "--scope",
        required=True,
        choices=["smoke", "sample", "main", "heavy", "implemented_but_not_run"],
    )
    parser.add_argument("--token-budget", required=True)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest-output", default="")
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--cache-dir", default="")
    parser.add_argument(
        "--token-counter-type",
        default="whitespace",
        choices=["whitespace", "character", "unknown", "future_bpe"],
    )
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _make_config(args)
    source = BUILDERS[args.dataset](config, root)
    try:
        manifest = source.prepare()
    except OptionalDatasetUnavailable as exc:
        if args.scope != "implemented_but_not_run":
            raise SystemExit(f"Dataset unavailable without fallback: {exc}") from exc
        manifest = source.write_manifest(
            records=[],
            output_path=None,
            implemented_but_not_run=True,
            notes=str(exc),
        )
    print(json.dumps({"manifest_path": config.manifest_path, "manifest": manifest}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
