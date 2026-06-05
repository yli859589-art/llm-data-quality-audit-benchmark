from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from registry_utils import read_registry_jsonl

REQUIRED_BASELINES = {
    "raw",
    "random_same_keep_rate",
    "length_filter",
    "dedup_only",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v3",
}
REQUIRED_SEEDS = {"1", "2", "3"}


def main() -> None:
    errors = []
    for row in read_registry_jsonl():
        if row["run_status"] != "completed_training":
            continue
        if row["dataset_key"] != "wikitext2_paper" or row["model_size"] != "small":
            continue
        if row["baseline_name"] not in REQUIRED_BASELINES or str(row["seed"]) not in REQUIRED_SEEDS:
            continue
        if int(row["train_steps"] or 0) < 300:
            errors.append(f"{row['run_id']} train_steps below 300")
        if int(row["train_tokens"] or 0) < 1_000_000:
            errors.append(f"{row['run_id']} train_tokens below 1,000,000")
        if int(row["validation_tokens"] or 0) < 50_000:
            errors.append(f"{row['run_id']} validation_tokens below 50,000")
        if int(row["evaluated_validation_tokens"] or 0) < 50_000:
            errors.append(f"{row['run_id']} evaluated_validation_tokens below 50,000")
    if errors:
        raise SystemExit("Training budget threshold check failed." + "\n" + "\n".join(errors))
    print("Training budget threshold check: ok")


if __name__ == "__main__":
    main()
