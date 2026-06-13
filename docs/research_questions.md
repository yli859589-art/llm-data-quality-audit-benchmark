# Research Questions

This document defines the research questions for the Level 3 upgrade path. It
does not add experiments or claim new results.

## RQ1: Filtering Under Fixed Token Budgets

Under fixed token budgets, do data filters outperform:

- raw data;
- seeded random retention at the same keep-rate;
- exact deduplication;
- length-based filtering;
- historical heuristic filters such as HDQS++?

The current evidence says raw remains strongest in the WikiText-2 official-split
small-model matrix, and HDQS++ v3 does not outperform raw under that fair
setting. Future work should preserve this negative evidence while testing
stronger filters and larger scopes.

## RQ2: Why and When Heuristic Filters Fail

When a heuristic filter fails, which mechanism explains the failure?

Candidate mechanisms:

- proxy-utility mismatch: the filter score captures surface cleanliness but not
  training utility;
- overfiltering: too much useful variation is removed;
- diversity loss: retained data becomes narrower than the raw distribution;
- domain shift: retained data no longer matches the validation domain;
- tokenizer sensitivity: gains or failures change under char-level versus BPE
  tokenization;
- scale-dependent ranking: a method that looks acceptable at one model scale
  may fail or reorder at another scale.

This question turns a negative result into research value. A filter that fails
cleanly and reproducibly can teach where the proxy breaks.

## RQ3: Future Utility-Risk-Diversity Selection

Future Level 3 work should test whether a Utility-Risk-Diversity selector can
produce a better Pareto frontier across:

- validation utility;
- duplication and contamination risk;
- PII or unsafe-content risk;
- topic and lexical diversity;
- compute and data-retention cost.

URD-Selector is not completed or verified in the current repository. It is a
future target that should only become a claim after implementation, registered
runs, fair baselines, and failure analysis.
