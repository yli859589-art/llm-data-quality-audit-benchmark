from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import csv
from collections import defaultdict

from experiment_utils import root


def main() -> None:
    path = root / "artifacts" / "tables" / "main_results.csv"
    if not path.exists():
        raise SystemExit("Missing artifacts/tables/main_results.csv")
    errors = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    for row in rows:
        if row["run_status"] != "completed_training":
            errors.append(f"{row['run_id']} is not completed_training")
        if row["dataset_status"] not in {"real_nonfallback", "real_local_nonfallback"}:
            errors.append(f"{row['run_id']} has impure dataset_status={row['dataset_status']}")
        if row["dataset_scope"] not in {"official_split", "full_dataset", "local_real_subset"}:
            errors.append(f"{row['run_id']} has impure dataset_scope={row['dataset_scope']}")
        if int(row["train_tokens"] or 0) < 1_000_000:
            errors.append(f"{row['run_id']} train_tokens below threshold")
        if int(row["evaluated_validation_tokens"] or 0) < 50_000:
            errors.append(f"{row['run_id']} evaluated_validation_tokens below threshold")
        for field in ["tokenizer_hash", "vocab_size", "parameter_count"]:
            if not row.get(field):
                errors.append(f"{row['run_id']} missing fairness field {field}")
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["dataset_key"], row["model_size"], row["seed"])].append(row)
    for group_key, group_rows in groups.items():
        for field in ["tokenizer_hash", "vocab_size", "parameter_count"]:
            values = {row[field] for row in group_rows}
            if len(values) > 1:
                errors.append(f"{group_key} has inconsistent {field}: {sorted(values)}")
    if errors:
        raise SystemExit("Main results purity check failed." + "\n" + "\n".join(errors))
    print(f"Main results purity check: ok ({len(rows)} rows)")


if __name__ == "__main__":
    main()
