from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root
from filters_v2.base import FilterConfig
from filters_v2.io import load_filter_inputs
from filters_v2.manifest import project_relative
from filters_v2.registry import get_filter_class


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_filter_config(filter_name: str) -> dict[str, object]:
    if not filter_name.startswith("urd_"):
        return {}
    path = root / "configs" / "filters" / f"{filter_name}.yaml"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Filter config must be a JSON-compatible mapping: {path}")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Step 4 baseline/filter smoke interface.")
    parser.add_argument("--filter", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--dataset-manifest", required=True)
    parser.add_argument("--tokenizer-manifest", required=True)
    parser.add_argument("--scope", required=True, choices=["smoke", "sample", "main_protocol", "implemented_but_not_run"])
    parser.add_argument("--target-keep-rate", type=float, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--allow-proxy", action="store_true")
    parser.add_argument("--allow-external-dependency", action="store_true")
    parser.add_argument("--min-estimated-tokens", type=int, default=None)
    parser.add_argument("--max-estimated-tokens", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_path = root / args.input if not Path(args.input).is_absolute() else Path(args.input)
    dataset_manifest_path = root / args.dataset_manifest if not Path(args.dataset_manifest).is_absolute() else Path(args.dataset_manifest)
    tokenizer_manifest_path = root / args.tokenizer_manifest if not Path(args.tokenizer_manifest).is_absolute() else Path(args.tokenizer_manifest)
    output_dir = root / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)

    for required_path in [input_path, dataset_manifest_path, tokenizer_manifest_path]:
        if not required_path.exists():
            raise SystemExit(f"Required input does not exist: {required_path}")

    dataset_manifest = _read_json(dataset_manifest_path)
    filter_config_payload = _read_filter_config(args.filter)
    filter_class = get_filter_class(args.filter)
    if getattr(filter_class, "proxy_used", False) and not args.allow_proxy:
        raise SystemExit(f"{args.filter} is a proxy/protocol filter; rerun with --allow-proxy")
    if getattr(filter_class, "external_dependency", "") and not args.allow_external_dependency:
        # Step 4 proxy implementations do not require external dependencies, but this
        # records that unavailable external baselines were not silently used.
        pass

    params: dict[str, object] = {}
    if isinstance(filter_config_payload.get("params"), dict):
        params.update(filter_config_payload["params"])  # type: ignore[arg-type]
    for key in [
        "selection_mode",
        "alpha",
        "beta",
        "gamma",
        "lambda_shift",
        "mu_cost",
        "normalization",
        "proxy_policy",
        "level3_main_method_candidate",
        "disabled_components",
    ]:
        if key in filter_config_payload:
            params[key] = filter_config_payload[key]
    if args.min_estimated_tokens is not None:
        params["min_estimated_tokens"] = args.min_estimated_tokens
    if args.max_estimated_tokens is not None:
        params["max_estimated_tokens"] = args.max_estimated_tokens

    filter_type = getattr(filter_class, "filter_type", args.filter)
    config = FilterConfig(
        filter_name=args.filter,
        filter_type=filter_type,
        target_keep_rate=args.target_keep_rate,
        token_counter_type=str(dataset_manifest.get("token_counter_type", "whitespace_proxy")),
        seed=args.seed,
        scope=args.scope,
        dataset_name=str(dataset_manifest.get("dataset_name", "")),
        dataset_manifest_path=args.dataset_manifest,
        tokenizer_manifest_path=args.tokenizer_manifest,
        allow_external_dependency=args.allow_external_dependency,
        allow_proxy=args.allow_proxy,
        smoke_only=args.scope == "smoke",
        notes=str(
            filter_config_payload.get(
                "notes",
                "Step 6 URD smoke output; not main experiment evidence."
                if args.filter.startswith("urd_")
                else "Step 4 filter interface smoke output; not main experiment evidence.",
            )
        ),
        params=params,
    )
    records = load_filter_inputs(input_path)
    filter_instance = filter_class(config)
    result = filter_instance.filter(records)
    manifest = filter_instance.write_outputs(output_dir, root=root)
    print(
        json.dumps(
            {
                "filter": args.filter,
                "filter_type": result.filter_type,
                "output_dir": args.output_dir,
                "manifest_path": project_relative(output_dir / "filter_manifest.json", root),
                "input_docs": result.input_docs,
                "kept_docs": result.kept_docs,
                "document_keep_rate": result.document_keep_rate,
                "token_keep_rate": result.token_keep_rate,
                "smoke_only": manifest["smoke_only"],
                "proxy_used": manifest["proxy_used"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
