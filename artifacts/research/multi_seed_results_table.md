# Multi-Seed Results Table

Mode: `paper-prototype` multi-seed.
Seed setting: `23,42,3407`.
Training budget: compact paper-prototype budget per seed/variant.
Interpretation: aggregate rows show direction and variance across seeds, not final paper-level significance.
Limitation note: confidence intervals are wide in the current small run.

| variant | metric | count | mean | std | ci95_low | ci95_high | bootstrap_ci_low | bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_pipeline | final_val_perplexity | 3 | 287764.94105306646 | 120974.50414482401 | 150869.402488199 | 424660.4796179339 | 180317.2825437217 | 418793.88762690773 |
| full_pipeline_without_hdqs | final_val_perplexity | 3 | 275532.6867047823 | 105193.80141459005 | 156494.69435974685 | 394570.6790498177 | 178483.30512878165 | 387317.15150312096 |
| hdqs_curriculum | final_val_perplexity | 3 | 289463.5262457789 | 93060.91172565435 | 184155.19107153534 | 394771.86142002244 | 197283.22924457138 | 383380.73742837174 |
| hdqs_filter | final_val_perplexity | 3 | 289463.5262457789 | 93060.91172565435 | 184155.19107153534 | 394771.86142002244 | 197283.22924457138 | 383380.73742837174 |
| raw_noisy_baseline | final_val_perplexity | 3 | 294610.2230331491 | 100636.375908921 | 180729.4431394326 | 408491.0029268656 | 204242.96380666696 | 403063.1105921097 |
