# Research Positioning

## Current Project Identity

The current repository is an experiment-candidate research artifact for auditing
LLM pretraining data-quality filters. Its value is not that the current
heuristic filter wins. Its value is that the project can run controlled
comparisons, preserve negative evidence, track artifacts, and enforce careful
public claims.

Current identity:

- Name: `LLM Data Quality Diagnostics and Risk Auditing Benchmark`
- Readiness: `EXPERIMENT-CANDIDATE`
- Method status: `honest_audit_framework`
- Benchmark scope status: `multi_dataset_audit_candidate`
- `ccf_c_ready`: `false`
- `ccf_b_ready`: `false`
- `level3_pipeline_ready`: `false`
- `level3_completed`: `false`

## Long-Term Level 3 Identity

The long-term target is `DataAudit-LM / URD-Selector`: a CCF-B-level research
prototype for language-model pretraining data filtering. The target should
eventually support multiple real datasets, multiple tokenizer/model scales,
strong baselines, a Utility-Risk-Diversity selector, broader evaluation metrics,
mechanism analysis, and stronger reproducibility evidence.

That target is a roadmap, not a current claim. The current repository should be
described as moving toward that target.

## Why Not Rewrite From Scratch

The repository already has assets that are expensive to rebuild:

- working tests;
- artifact registry and run registry;
- dataset manifests;
- no-fallback and split-integrity checks;
- claim hygiene checks;
- release checks;
- real non-fallback WikiText-2 data flow;
- bounded OpenWebText/C4 streaming-sample audit evidence;
- baseline/filter/scoring code;
- failure analysis and negative-result documentation;
- reproducibility and release documentation.

Throwing these away would weaken traceability. The correct upgrade strategy is
to preserve the audit backbone, isolate legacy education modules, and upgrade
the main research pipeline in stages.

## Preserve, Refactor, Legacy, Replace

| Area | Current value | Action | Reason |
|---|---|---|---|
| Tests | Regression protection and evidence that wrappers run | Preserve | Tests are part of the current trust boundary. |
| Artifact registry | Links results to scripts and status | Preserve and strengthen | Future results need stronger lineage, not less. |
| Dataset manifests | Identify fallback, split, and data status | Preserve and upgrade | Step 2 depends on manifest discipline. |
| Run registry | Append-oriented experiment history | Preserve | Negative and failed runs are evidence. |
| Claim hygiene | Prevents overstated public wording | Preserve and extend | Level 3 will need stricter claim boundaries. |
| HDQS++ | Useful historical baseline and failure object | Refactor role | Keep it, but do not present it as the final method. |
| Course modules | Educational and algorithmic history | Legacy isolate | Useful, but not the DataAudit-LM mainline. |
| Main training pipeline | Small-model candidate benchmark | Refactor | Needs tokenizer/model-scale upgrades before URD-Selector. |
| Smoke/fallback paths | Engineering checks | Legacy or isolate from claims | Useful for fast tests, unsafe for main evidence. |

## HDQS++ Role

HDQS++ should remain in the repository as a historical baseline and
failure-analysis object. Current evidence shows HDQS++ v3 improves over earlier
HDQS++ variants trend-wise, but does not outperform raw under the fair
WikiText-2 small-model setting.

That negative result is useful. It motivates the future Utility-Risk-Diversity
direction by showing that intuitive heuristic quality scores can fail when they
overfilter, shift the distribution, or optimize a proxy that does not match
training utility.

## URD-Selector Future Main Method

URD-Selector is the intended future main method, not an implemented current
claim. It should only become a method claim after:

- the dataset pipeline is upgraded;
- tokenizer and model-scale settings are stable;
- strong baselines are implemented and fairly matched;
- training and evaluation are reproducible;
- results are recorded through the registry;
- failure cases and negative evidence are preserved.

## Current Evidence Boundary

Current evidence supports:

- real non-fallback WikiText-2 official-split small-model audit evidence;
- bounded streaming-sample OpenWebText/C4 audit evidence;
- raw/random/dedup/length/HDQS++ comparisons inside recorded scopes;
- negative evidence that HDQS++ v3 does not outperform raw in the current fair
  WikiText-2 setting;
- artifact lineage and claim-hygiene discipline.

Current evidence does not support:

- CCF-B readiness;
- completed Level 3 status;
- full OpenWebText/C4 results;
- large-scale LLM pretraining conclusions;
- completed downstream evaluation;
- verified URD-Selector performance.

## Future CCF-B Level 3 Target Boundary

The future target is a CCF-B-level artifact, but the phrase should be used as an
upgrade target only. The project can move toward that level after it adds
stronger data scope, tokenizer/model scale, baselines, metrics, analysis, and
release evidence.
