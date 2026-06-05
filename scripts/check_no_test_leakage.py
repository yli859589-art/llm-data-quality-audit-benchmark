from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root


def main() -> None:
    errors: list[str] = []
    frozen_path = root / "artifacts" / "frozen" / "hdqspp_frozen_wikitext2.json"
    report_path = root / "artifacts" / "frozen" / "hdqspp_freezing_report.md"
    if not frozen_path.exists():
        errors.append(
            "Missing real dev frozen artifact: "
            "artifacts/frozen/hdqspp_frozen_wikitext2.json"
        )
        frozen = {}
    else:
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if not report_path.exists():
        errors.append("Missing freezing report")
        report_text = ""
    else:
        report_text = report_path.read_text(encoding="utf-8")

    if frozen.get("dataset_key") != "wikitext2_paper":
        errors.append("Frozen config must target wikitext2_paper")
    if frozen.get("selection_split") != "dev":
        errors.append("Frozen config selection_split must be dev")
    if frozen.get("test_split_used_for_selection") is not False:
        errors.append("Frozen config must state test split was not used for selection")
    if not frozen.get("source_run_ids"):
        errors.append("Frozen config missing source_run_ids")
    if not frozen.get("tokenizer_hash") or not frozen.get("vocab_size"):
        errors.append("Frozen config missing tokenizer/vocab evidence")
    if int(frozen.get("evaluated_validation_tokens", 0) or 0) < 50_000:
        errors.append("Frozen config evaluated_validation_tokens below threshold")
    required_phrases = [
        "No test leakage",
        "test split was not used",
        "Source run IDs",
        "Tokenizer hash",
    ]
    for phrase in required_phrases:
        if phrase not in report_text:
            errors.append(f"freezing report missing phrase: {phrase}")

    output = root / "artifacts" / "frozen" / "no_test_leakage_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "status": "failed" if errors else "passed",
                "errors": errors,
                "checked_by": "scripts/check_no_test_leakage.py",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if errors:
        raise SystemExit("No-test-leakage check failed." + "\n" + "\n".join(errors))
    print("No-test-leakage check: ok")


if __name__ == "__main__":
    main()
