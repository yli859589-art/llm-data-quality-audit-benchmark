# Claim Artifact Map

| Claim | Artifact | Support level | Boundary |
|---|---|---|---|
| The benchmark pipeline is executable in smoke mode. | `artifacts/quick_experiment/REPORT.md`; `artifacts/data/wikitext2_smoke/data_manifest.json` | Supported | Smoke/local fixture scale only. |
| Paper/full configs forbid fallback. | `configs/experiments/paper_*.yaml`; `configs/data/*_paper.yaml`; `scripts/check_no_fallback_in_experiments.py` | Supported | Config-level guard; real-data runs still pending. |
| Baseline infrastructure exists. | `scripts/run_baselines.py`; `artifacts/runs/run_registry.csv`; `artifacts/baselines/` | Supported after generation | Data-filter metrics, not model-quality proof. |
| HDQS++ can be frozen before test evaluation. | `scripts/freeze_hdqspp.py`; `artifacts/frozen/` | Supported after generation | Smoke split hashes are not paper-scale evidence. |
| Ablations are available. | `scripts/run_ablation.py`; `artifacts/ablations/smoke/ablation_results.csv` | Supported after generation | Data-filter ablation unless model metrics are added. |
| Multi-seed model improvement is statistically significant. | `artifacts/stats/claim_safety_report.md` | Unsupported | Needs real multi-seed validation/perplexity metrics. |
| The project is ready for CCF-C submission. | `artifacts/experiment_readiness_report.json` | Unsupported | Readiness checker should remain below final level until full experiments finish. |
