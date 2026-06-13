from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json

from experiment_utils import root
from tokenization.budget import build_token_budget_report, write_token_budget_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Step 3 tokenizer-specific token budget report.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--tokenizer-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = json.loads((root / args.tokenizer_manifest).read_text(encoding="utf-8"))
    report = build_token_budget_report(data_path=root / args.data, tokenizer_manifest=manifest, root=root)
    write_token_budget_report(root / args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
