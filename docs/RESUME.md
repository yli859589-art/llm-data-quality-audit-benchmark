# Resume-Safe Project Description

## English

**LLM Data Quality Benchmark Platform | Python / PyTorch / NumPy**

- Built a reproducible benchmark for small-scale language-model pretraining
  data quality, including deterministic noise injection, PII redaction, exact
  deduplication, Jaccard and MinHash/LSH near-duplicate detection, HDQS
  document-quality scoring, equal-budget ablations, and an auxiliary attention
  systems benchmark.
- Implemented script-generated reports, JSON/CSV artifacts, SVG
  visualizations, unit/numerical/regression tests, source-coverage reporting,
  GitHub Actions CI, repository hygiene checks, and offline quick-mode
  reproducibility.
- Verified the deterministic quick stress test as a single-seed CPU smoke
  benchmark and observed preliminary perplexity improvement for the full
  pipeline over the raw noisy baseline; larger multi-seed, multi-dataset
  experiments remain future work.

## 中文

**LLM 数据质量基准平台 | Python / PyTorch / NumPy**

- 构建小规模语言模型预训练数据质量 Benchmark，支持确定性噪声注入、PII 脱敏、
  精确去重、Jaccard/MinHash 近重复检测、HDQS 文档质量评分、等预算训练消融和
  辅助注意力系统基准。
- 实现可复现实验脚本、单元/数值/回归测试、源码覆盖率统计、GitHub Actions CI、
  仓库卫生检查，以及脚本生成的 JSON/CSV 实验报告与 SVG 可视化。
- 在 deterministic quick stress test 中验证数据处理流程可复现，并观察到 full
  pipeline 相比 raw noisy baseline 有初步 perplexity 改善；多数据集、多随机种子
  full matrix 仍属于后续工作。

## Claim Boundary

Use this as a personal research-oriented GitHub project or a CCF-C paper
direction research prototype. Do not describe it as a completed CCF-C paper
project, official coursework, a competition award, an accepted paper, or
evidence of private-grader completion.
