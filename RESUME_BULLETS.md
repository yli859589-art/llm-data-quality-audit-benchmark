# Resume Bullets

Use these bullets only with the reporting boundary in
`docs/REPORTING_CONTRACT.md`.

## English

- Built a reproducible LLM data quality audit benchmark with real non-fallback
  data pipelines, append-only run registry, artifact lineage, multi-seed
  baselines, split-integrity checks, no-test-leakage validation, and
  cross-dataset streaming audit over WikiText-2, OpenWebText sample, and C4
  sample.
- Found that heuristic quality filters such as HDQS++ can underperform raw/dedup
  baselines under fair tokenizer/model/evaluation settings, highlighting risks
  of unverified data filtering in LLM pretraining.
- Implemented release-grade validation including claim hygiene, reproducibility
  checks, fresh-unzip verification, dataset manifests, and cross-dataset status
  reporting.

## Chinese

- 构建了一个可复现的 LLM 数据质量审计 benchmark，包含真实非 fallback
  数据管线、append-only run registry、artifact lineage、多 seed baseline、
  split-integrity、no-test-leakage 检查，以及 WikiText-2、OpenWebText sample
  和 C4 sample 的 cross-dataset streaming audit。
- 发现 HDQS++ 等启发式质量过滤方法在公平 tokenizer/model/evaluation
  设置下可能弱于 raw/dedup baseline，说明未经验证的数据过滤可能伤害 LLM
  预训练效果。
- 实现了面向发布的验证链路，包括 claim hygiene、reproducibility checks、
  fresh-unzip verification、dataset manifests 和 cross-dataset status
  reporting。

## Safe Boundary

HDQS++ v3 does not outperform raw under the current fair benchmark.

## Do Not Write These Forbidden Claims

- Developed a state-of-the-art filter.
- Improved LLM pretraining perplexity.
- Beat raw baseline.
- CCF-C-ready project.
