# Technical Overview

- Tokenizer: GPT-2 BPE.
- Datasets: OpenWebText V2 100M and C4 English V2 100M.
- Model: small decoder LM, context length 256.
- Training: 489 steps/run, 1,001,472 tokens_seen/run.
- Evaluation: valid NLL, log-PPL/PPL, paired seed differences, bootstrap CI, risk/diversity/cost, Pareto diagnostics.
