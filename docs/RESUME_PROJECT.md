# DataAudit-LM Resume Project

## English Title

DataAudit-LM: Reproducible Benchmark for LLM Pretraining Data Filtering

## 中文标题

DataAudit-LM：大语言模型预训练数据质量审计基准

## Resume Description

Built a reproducible benchmark for auditing LLM pretraining-data filtering on
real OpenWebText and C4 samples. Implemented independent filtering methods,
controlled multi-seed decoder-LM training, per-run lineage tracking, per-token
NLL/PPL metric audits, statistical summaries, downstream probes, and artifact
integrity checks.

Current verified evidence includes 2 datasets, 200006900 GPT-2 source tokens,
7 filtering methods, 3 seeds, 42 completed controlled training runs, 5001216
tokens per run, 210051072 aggregate tokens seen, and a 20542752-parameter
small decoder language model.

The project preserves mixed and negative findings instead of presenting a
single method as universally superior.
