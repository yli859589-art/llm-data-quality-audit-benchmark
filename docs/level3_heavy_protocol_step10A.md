# Step 10A Level 3 Heavy Protocol Freeze

Step 10A freezes the future heavy-execution protocol for the Level 3 route. It
does not download large corpora, train models, run downstream benchmarks, or add
new PPL/downstream numbers.

## Scope

- Canonical configs: `configs/level3/`.
- Protocol checks: `scripts/check_level3_protocol.py` and
  `scripts/check_level3_preflight.py`.
- Dry-run execution plans: `scripts/level3/`.
- Readiness report: `artifacts/reports/step10A_readiness_report.json`.

## Boundary

Step 10A allows only these claims:

- the Level 3 heavy protocol is frozen;
- data, tokenizer, filter, training, evaluation, mechanism, statistics, compute,
  and artifact-path matrices are specified;
- the repository remains `LEVEL3_PIPELINE_READY`;
- heavy evidence is not completed.

Step 10A does not support method-effectiveness claims, CCF readiness claims, or
completed Level 3 claims.

## Next Stage

Step 10B may execute the heavy data and model pipeline only after the protocol
and preflight checks pass and resources are confirmed.

