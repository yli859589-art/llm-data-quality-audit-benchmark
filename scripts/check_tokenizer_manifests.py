from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path

from experiment_utils import root
from tokenization.validation import TokenizerManifestError, validate_tokenizer_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Step 3 tokenizer manifests.")
    parser.add_argument("--path", default="artifacts/tokenizers_step3")
    args = parser.parse_args()

    base = root / args.path
    manifests = sorted(base.glob("**/tokenizer_manifest.json")) if base.exists() else []
    errors: list[str] = []
    for path in manifests:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            validate_tokenizer_manifest(manifest, root)
        except (json.JSONDecodeError, TokenizerManifestError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")

    report = {
        "status": "failed" if errors else "passed",
        "checked_manifests": len(manifests),
        "errors": errors,
    }
    output = root / "artifacts" / "reports" / "tokenizer_manifest_check_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if errors:
        raise SystemExit("Tokenizer manifest check failed.\n" + "\n".join(errors))
    print(f"Tokenizer manifest check: ok ({len(manifests)} manifests)")


if __name__ == "__main__":
    main()
