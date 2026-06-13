# Step 0 Repository Audit Before Level 3 Upgrade

Date: 2026-06-10

Audit target: the current checked-out repository root.

Long-term target, not executed in this step:
`DataAudit-LM / URD-Selector`, a CCF-B-level research prototype for
multi-dataset, multi-scale, multi-baseline, reproducible and explainable
language-model pretraining data filtering.

This Step 0 audit does not refactor the project, does not add URD-Selector, does
not add new experiments, does not modify `main_results.csv`, and does not change
the current reporting boundary.

## 1. Executive Summary

The repository is a credible experiment-candidate audit benchmark rather than a
blank slate. It already has useful research-engineering assets: real
non-fallback data manifests, an append-oriented run registry, main-result purity
checks, claim-hygiene checks, artifact-lineage checks, multi-seed WikiText-2
training evidence, cross-dataset streaming-sample evidence, failure analysis,
release verification, tests, CI, and reproducibility documentation.

Current status remains:

- Readiness: `EXPERIMENT-CANDIDATE`
- Method status: `honest_audit_framework`
- Benchmark scope status: `multi_dataset_audit_candidate`
- `ccf_c_ready`: `false`

The project should not be judged as needing a full rewrite. The right strategy
is to preserve the existing audit/reproducibility backbone, isolate legacy
course-suite assets, and upgrade the research mainline in phases.

The most important current limitation is not code execution. The main limitation
is research scope: the primary model pipeline is still small-scale and mainly
character-tokenized; OpenWebText/C4 evidence is bounded streaming-sample
evidence; several stronger external baselines are only smoke/proxy-level or not
implemented; and evaluation is still centered on validation perplexity plus
diagnostic artifacts rather than a full Level 3 research evaluation suite.

## 2. Current Repository Structure

Top-level project assets include:

| Area | Current contents | Audit note |
|---|---|---|
| `src/` | 74 Python source files across benchmark, data, filters, stats, diagnostics, and legacy course modules | Main LLM audit code is present; legacy course modules should be isolated, not deleted. |
| `scripts/` | 71 executable/check/generation scripts | Strong experiment and release wrapper layer. |
| `tests/` | 13 test files, 69 collected tests | Tests pass in the current environment. |
| `configs/` | data, dataset, experiment, filter, frozen, and model configs | Main and streaming configs are separated; medium/BPE configs exist but are not current main evidence. |
| `docs/` | 50+ Markdown/CSV/JSON documentation artifacts | Strong claim boundary and reproducibility documentation. |
| `artifacts/` | data manifests, run registry, tables, stats, figures, diagnostics, release reports | Valuable audit trail; should be preserved. |
| `.github/workflows/ci.yml` | GitHub Actions workflow | CI exists, but should be revisited after Level 3 restructuring. |
| `pyproject.toml` | setuptools package config | Supports editable install. |
| `requirements*.txt` | runtime and dev dependencies | No Docker or conda environment file found. |

Observed repository scale:

- Python files: 163
- Script files: 71
- Test files: 13
- Markdown docs: about 150
- Source lines under `src/`: about 6.2k
- Test lines under `tests/`: about 0.9k

Main `src/` modules:

- `course_project_suite/llm_benchmark/`: current benchmark, data quality,
  char LM training, dataset matrix, dedup, privacy, statistics, reporting.
- `data/`: real corpus loading, HuggingFace/streaming loaders, manifests,
  dataset cards, split utilities, token counting.
- `filters/`: HDQS++ v2/v3 and scoring calibration.
- `baselines/`: baseline filtering suite.
- `analysis/`, `diagnostics/`, `stats/`, `scoring/`: error analysis,
  significance, frozen protocol support, and failure diagnostics.
- `course_project_suite/cs188`, `cs224n`, `cs231n`, `cs336`, `d2l`,
  `coursera_ml`: useful educational/legacy assets; not the current research
  mainline.

Executable script categories:

- Data preparation: `prepare_real_data.py`, `prepare_streaming_data.py`,
  `fetch_public_data.py`.
- Experiment runners: `run_experiment.py`, `run_baselines.py`,
  `run_dataset_matrix.py`, `run_multi_seed.py`, `run_model_scaling.py`,
  `run_ablation.py`, `run_v3_ablation.py`.
- Analysis/generation: `analyze_significance.py`,
  `generate_cross_dataset_tables.py`, `analyze_cross_dataset_audit.py`,
  `generate_tables.py`, `generate_figures.py`,
  `generate_project_dashboard.py`, `generate_method_dashboard.py`.
- Checks: `check_repo.py`, `check_registry_schema.py`,
  `check_artifact_lineage.py`, `check_main_results_purity.py`,
  `check_no_fallback_in_experiments.py`, `check_no_test_leakage.py`,
  `check_split_integrity.py`, `check_claim_hygiene.py`,
  `check_experiment_readiness.py`, `run_all_checks.py`,
  `run_release_checks.py`, `verify_fresh_unzip.py`.

Packaging and environment:

- `pip install -e .` is supported and passed.
- CI exists at `.github/workflows/ci.yml`.
- No `Dockerfile`, `docker-compose.yml`, conda `environment.yml`, or
  `.devcontainer` was found.

## 3. Existing Data Pipeline

Current supported dataset/config families:

- `wikitext2_paper`
- `wikitext2_smoke`
- `openwebtext_streaming`
- `openwebtext_smoke`
- `c4_en_streaming`
- `c4_en_smoke`
- older dataset-matrix configs such as `local_wikitext_sample`,
  `synthetic_web_noise`, `tiny_shakespeare`, `mixed_debug`,
  `openwebtext_sample`, and `c4_sample`.

Real non-fallback state:

- `wikitext2_paper`: `real_local_nonfallback`, `official_split`.
- `openwebtext_streaming`: `real_nonfallback`, `streaming_sample`.
- `c4_en_streaming`: `real_nonfallback`, `streaming_sample`.

Manifest state:

- Main manifests exist under `artifacts/data/<dataset>/data_manifest.json`.
- WikiText-2 manifest includes split/document hash information and official
  split scope.
- Streaming manifests include content hashes, command, config path, split files,
  document counts, token counts, and `allow_fallback: false`.
- Dataset cards exist for the main real-data artifacts.

Checks already present:

- `scripts/check_split_integrity.py`
- `scripts/check_no_fallback_in_experiments.py`
- `scripts/check_no_test_leakage.py`
- `scripts/check_main_results_purity.py`
- `scripts/check_artifact_lineage.py`

Current result origin:

- `artifacts/tables/main_results.csv` exists and contains 24 rows.
- It includes only the WikiText-2 official-split small-model candidate matrix:
  8 methods x 3 seeds.
- Cross-dataset OpenWebText/C4 evidence is separated into
  `artifacts/cross_dataset/`, not mixed into `main_results.csv`.
- Registry rows include commands, config paths, config hashes, manifest paths,
  artifact paths, artifact hashes, tokenizer hashes, vocabulary sizes, parameter
  counts, train tokens, and evaluated validation-token budgets.

Fallback risk assessment:

- No fallback was found in the current main/cross-dataset completed evidence.
- `run_all_checks.py` passed the no-fallback check.
- Legacy/smoke/dataset-matrix code paths still support fallback-style adapters
  or fallback reports. This is acceptable for smoke mode but should be clearly
  isolated before Level 3 so smoke/fallback assets cannot be mistaken for main
  evidence.

## 4. Existing Tokenizer and Model Pipeline

Current primary tokenizer:

- The main training path uses a shared character vocabulary via `CharVocab` in
  `src/course_project_suite/llm_benchmark/char_lm.py`.
- Main-result rows record `tokenizer_type`, `tokenizer_id`, `tokenizer_hash`,
  `vocab_size`, and `parameter_count`.
- There is no standalone tokenizer manifest file comparable to the dataset
  manifests. Tokenizer provenance is currently embedded in metrics/registry
  fields.

BPE / GPT-style tokenizer state:

- A minimal `BPETokenizer` exists in `src/course_project_suite/cs336/tokenizer.py`.
- BPE model configs exist, for example `configs/models/bpe_small_gpt.yaml` and
  `configs/models/bpe_tiny_gpt.yaml`.
- These are not the current primary evidence path and should not be described as
  a completed production tokenizer pipeline.

Model state:

- The main training loop calls a compact decoder-only `MiniGPT2` through
  `train_character_lm`.
- Current main WikiText-2 `small` configuration is:
  6 layers, hidden size 384, 6 attention heads, context length 512 in the model
  config, with experiment training using block size 256.
- Main WikiText-2 rows report parameter count `10854528`.
- OpenWebText/C4 streaming rows report slightly different parameter counts due
  to dataset-specific character vocabularies.

Scale support:

- `tiny` and `small` configs exist and are operational.
- `medium` and optional BPE/medium configs exist, but are marked as future or
  optional target configurations, not current evidence.
- No completed large-lite or robust medium-scale evidence is present.

Reproducibility:

- Training scripts are seed-controlled.
- Multi-seed support exists and is used for the main matrix.
- Metrics JSON files contain training curves for individual runs.
- Some dataset-matrix artifacts include `training_curves.csv` and SVGs.
- A dedicated checkpoint manifest is not present. The training config has an
  optional checkpoint path hook, but checkpoint provenance is not yet a Level 3
  feature.

## 5. Existing Filtering Methods and Baselines

Methods present in current or legacy/filtering code:

| Method | Current state |
|---|---|
| `raw` | Present and central. Strongest/tied baseline in current evidence. |
| `random_same_keep_rate` | Present; seeded random retention. |
| `dedup_only` | Present; exact dedup baseline. |
| `length_filter` | Present; included in main WikiText-2 matrix. |
| `hdqspp` / HDQS++ v1 | Present; should be kept as historical baseline/failure-analysis object. |
| `hdqspp_v2` | Present; distribution-preserving quality heuristic. |
| `hdqspp_v2_no_token_frequency` | Present as diagnostic variant. |
| `hdqspp_v3` | Present; current audited candidate, not a supported winner. |
| C4/Gopher-style heuristic | Present as `c4_gopher_heuristic` in baseline suite/smoke artifacts; not part of the main training matrix. |
| Perplexity filter | Only an n-gram proxy `perplexity_quality_ngram` exists; no neural LM perplexity filter. |
| Independent quality score | Present as a simple lexical/length/symbol proxy. |
| Optional external wrapper | Present but configured as skipped/incomplete without external command. |
| CCNet-style filter | Not implemented as a named full baseline. |
| Classifier filter | Not implemented as a real trained classifier baseline. |
| Embedding diversity filter | Not implemented as a real embedding/diversity selector. |

Filter output state:

- `run_baseline` returns retained documents plus a `BaselineResult`.
- Baseline artifacts write `metrics.json` and retained samples.
- Training experiment selection returns documents and retention rate.
- There is not yet one unified Level 3 filter-output manifest schema shared by
  all methods, all datasets, and all model scales.

Keep-rate fairness:

- The project uses `target_keep_rate` for random and length baselines and uses
  retention settings for HDQS++ variants.
- Main model comparisons also enforce shared tokenizer/model/evaluation budgets.
- For Level 3, keep-rate fairness should be made explicit as a first-class
  filter contract: target keep-rate, actual keep-rate, token keep-rate, document
  keep-rate, and budget normalization should all be represented in a manifest.

## 6. Existing Evaluation Metrics

Current main metric:

- Final validation perplexity is the primary model-quality metric.
- Main WikiText-2 results use multi-seed small-model dev evidence.

Existing supporting metrics and analyses:

- Bootstrap CI and paired difference analysis exist in
  `scripts/analyze_significance.py` and `artifacts/stats/`.
- Failure analysis exists for HDQS++ behavior, component correlations,
  distribution shift, and method error cases.
- Diversity/proxy metrics exist in quality scoring and dataset-matrix artifacts.
- Privacy/PII-style metrics exist in baseline/result helper code and
  dataset-matrix artifacts.
- Cost/system metrics exist at run level in limited form, such as
  `tokens_per_second` and optional CUDA memory fields.
- Dataset-matrix artifacts include quick-mode downstream/proxy reports,
  retention Pareto rows, privacy-utility tradeoff, generation quality reports,
  and training curves.

Missing or incomplete for CCF-B Level 3:

- No robust downstream task evaluation.
- No rank-stability analysis across datasets/seeds/scales.
- No full Pareto frontier across quality, diversity, cost, and model utility in
  the current mainline.
- No real classifier, embedding-diversity, CCNet, or neural perplexity baseline.
- No medium/large-lite replicated model-scale evaluation.
- No complete mechanism analysis tying filter decisions to model-gradient,
  domain, or token-distribution effects beyond current diagnostics.

## 7. Existing Artifacts and Results

Important artifacts to preserve:

- `artifacts/runs/run_registry.jsonl`
- `artifacts/runs/run_registry.csv`
- `artifacts/runs/migration_log.jsonl`
- `artifacts/tables/main_results.csv`
- `artifacts/stats/main_results.csv`
- `artifacts/stats/significance_tests.csv`
- `artifacts/stats/method_status_report.md`
- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/cross_dataset/dataset_status_matrix.csv`
- `artifacts/data/*/data_manifest.json`
- `artifacts/diagnostics/*`
- `artifacts/release/*`

Main result state:

- `main_results.csv` exists.
- It has 24 rows from `wikitext2_paper`.
- `check_main_results_purity.py` passed.
- The current SHA-256 observed during audit:
  `eab3478d19e04caf97e07fc31fcd3cc36089c19320a64e96f7bac9eb12d89921`.

Cross-dataset state:

- `wikitext2_paper`: 12 completed cross-dataset rows, 0 failed rows.
- `openwebtext_streaming`: 12 completed rows, 0 failed rows.
- `c4_en_streaming`: 12 completed rows, 0 failed rows.

Canonical result interpretation remains negative/diagnostic:

- Raw is strongest on the current WikiText-2 mean-PPL matrix.
- Raw/dedup are strongest or tied-strongest in the current streaming-sample
  evidence.
- HDQS++ v3 improves over earlier HDQS++ trend-wise but does not beat raw.

## 8. Existing Tests and Reproducibility Checks

Test files:

- `tests/test_algorithm_edges.py`
- `tests/test_clean_artifacts.py`
- `tests/test_data_quality_research.py`
- `tests/test_dataset_matrix.py`
- `tests/test_datasets.py`
- `tests/test_experiment_infrastructure.py`
- `tests/test_hdqs_scoring.py`
- `tests/test_llm_benchmark.py`
- `tests/test_near_dedup.py`
- `tests/test_research_artifacts.py`
- `tests/test_smoke.py`
- `tests/test_statistics.py`
- `tests/test_supporting_edges.py`

Verification commands run in this Step 0 audit:

| Command | Result |
|---|---|
| `python -m pip install -e .` | Passed |
| `python -m pytest tests/ -q` | Passed, 69 tests |
| `python scripts/run_all_checks.py --timeout 300` | Passed |
| `python -m json.tool artifacts/reports/step0_readiness_report.json` | Passed |
| `python scripts/check_claim_hygiene.py` | Passed |
| `python scripts/check_repo.py --clean` | Passed |

`run_all_checks.py` executed:

- repository hygiene and cache cleanup
- pytest
- environment fingerprint capture
- registry schema check
- artifact lineage check
- main-results purity check
- training-budget threshold check
- config downgrade check
- split integrity check
- no-test-leakage check
- no-fallback check
- claim support check
- experiment readiness check
- claim hygiene check

No tracked files were modified by these checks before the Step 0 report files
were added. Cache/temp cleanup removed generated paths only.

## 9. Existing Claim Boundary

Claim boundary is one of the strongest existing assets.

Key files:

- `docs/REPORTING_CONTRACT.md`
- `docs/PROJECT_STATUS.md`
- `docs/LIMITATIONS.md`
- `docs/CROSS_DATASET_AUDIT.md`
- `artifacts/release/claim_hygiene_report.json`
- `artifacts/release/final_release_report.md`

Current public claim is appropriately bounded:

- The project is an audit benchmark.
- It does not claim institutional affiliation, official coursework completion,
  competition placement, publication acceptance, or supported improvement over
  raw training data.
- It explicitly states that HDQS++ v3 does not outperform raw under the current
  fair benchmark.
- It explicitly states that OpenWebText/C4 rows are streaming-sample audits, not
  full upstream dataset results.

Claim-hygiene tooling:

- `scripts/check_claim_hygiene.py` scans dangerous phrases.
- `scripts/check_claims_supported.py` checks supported claims.
- `scripts/check_artifacts.py` exists for artifact checks.
- `scripts/check_main_results_purity.py` protects main result purity.

Risks still present:

- `main_results.csv` is a committed CSV artifact. It is protected by checks, but
  a future manual edit could still be attempted. Level 3 should strengthen
  registry-to-table regeneration and hash-locking.
- Smoke/filtering artifacts coexist with main results. The current checks keep
  them separate, but future refactoring must preserve that separation.
- Future CCF-B wording can easily drift into unsupported claims if claim hygiene
  is not extended to the new naming.

## 10. What Should Be Preserved

The following assets should be protected during Level 3 work:

1. Existing tests and test fixtures.
2. Append-oriented artifact/run registry.
3. Claim hygiene and reporting contract.
4. Dataset manifests and dataset cards.
5. Real non-fallback WikiText-2/OpenWebText/C4 data flow.
6. `check_*` and release-wrapper scripts.
7. Baseline/filter/scoring code, especially raw/random/dedup/length/HDQS++.
8. Negative result and HDQS++ failure analysis.
9. Cross-dataset separation between main and streaming-sample evidence.
10. Reproducibility docs and release reports.

## Preserve / Refactor / Legacy / Replace Matrix

| Module | Current Value | Preserve / Refactor / Legacy / Replace | Reason | Risk if Removed | Upgrade Recommendation |
|---|---|---|---|---|---|
| `artifacts/runs/run_registry.*` | Core experiment provenance | Preserve | Tracks commands, configs, manifests, metrics, hashes, failed/superseded runs | Losing audit trail and negative evidence | Keep append-only; add stronger registry-to-table reproducibility checks. |
| `artifacts/tables/main_results.csv` | Canonical current WikiText-2 result table | Preserve | Stable baseline for comparison and claim boundary | Losing current evidence baseline | Freeze as Step 0 baseline; never hand-edit; regenerate only through scripts. |
| `docs/REPORTING_CONTRACT.md` | Public claim boundary | Preserve | Prevents unsupported method-success claims | Claim drift toward false CCF-B readiness | Extend in Step 1 for Level 3 wording, do not delete. |
| `scripts/check_claim_hygiene.py` | Claim safety gate | Refactor | Useful but phrase list is CCF-C-era and HDQS++-specific | Unsupported new URD-Selector claims may slip through | Add CCF-B/URD-specific dangerous phrases later. |
| `scripts/run_all_checks.py` and `scripts/subprocess_utils.py` | Stable wrapper checks | Preserve | Cross-platform timeout runner works and passed | Regression in reproducibility workflow | Keep as release gate; add Level 3 checks incrementally. |
| `src/data/*` | Real corpus, manifest, split utilities | Refactor | Strong base for multi-dataset data pipeline | Rebuilding data lineage from scratch | Generalize manifests to Level 3 dataset registry. |
| `artifacts/data/*/data_manifest.json` | Dataset provenance | Preserve | Records status, scope, hashes, token counts | Fallback/sample confusion | Add tokenizer/filter/checkpoint manifest links. |
| `src/course_project_suite/llm_benchmark/char_lm.py` | Working small LM training loop | Refactor | Good smoke/small baseline but char-level only | Losing runnable baseline training | Keep as small baseline; add BPE/GPT tokenizer pipeline separately. |
| `src/course_project_suite/cs336/tokenizer.py` | Minimal BPE teaching implementation | Legacy | Useful reference, not production Level 3 tokenizer | Confusing prototype with main tokenizer | Keep under legacy; replace main tokenizer path with robust BPE/GPT-2-compatible option later. |
| `configs/models/small.yaml` | Current main model config | Preserve | Existing results depend on it | Invalidating current result matrix | Freeze as small baseline config. |
| `configs/models/medium*.yaml` | Future model-scale configs | Refactor | Useful target but not current evidence | False claim of medium-scale support | Move into explicit planned/experimental configs until executed. |
| `src/baselines/data_quality_baselines.py` | Existing baseline suite | Refactor | Contains raw/random/dedup/length and proxy baselines | Losing baseline breadth | Normalize outputs into one filter manifest schema. |
| `src/filters/hdqspp_v2.py`, `hdqspp_v3.py` | Historical audited candidate filters | Refactor | Important negative-result and failure-analysis object | Erasing negative evidence | Reposition as historical baselines, not primary winning method. |
| `src/diagnostics/hdqspp_failure.py` and diagnostics artifacts | Mechanism/failure evidence | Preserve | Shows why filtering can fail | Project becomes only score table | Expand to URD/general filter diagnostics. |
| `scripts/analyze_significance.py` | Bootstrap/paired comparison | Refactor | Useful seed-aware analysis | Weak statistical claims | Add rank stability, dataset-level random effects, and stronger paired tests. |
| `artifacts/cross_dataset/*` | Multi-dataset audit evidence | Preserve | Separates streaming samples from main result | Full-dataset claim confusion | Keep scope labels; add larger samples later. |
| `projects/cs188`, `projects/cs231n`, `projects/cs224n`, `projects/d2l`, `projects/cs336` | Educational portfolio assets | Legacy | Not part of the Level 3 research mainline | Deleting may remove useful examples/history | Move to `legacy/` or document as archived support material later. |
| `src/course_project_suite/cs188`, `cs224n`, `cs231n`, `d2l`, `coursera_ml` | Course-inspired algorithm implementations | Legacy | Useful but dilutes research repository focus | Import/test breakage if abruptly deleted | Isolate behind legacy namespace and keep tests until replacement plan exists. |
| `docs/future_publication_notes/*` | Future gap notes | Legacy/Preserve | Useful roadmap but not current claim | Reviewer confusion if mixed with release claims | Keep archival labeling; do not cite as current result. |
| `.github/workflows/ci.yml` | CI skeleton | Refactor | Existing CI proves intent, but may not match Step 0 commands exactly | False confidence from stale CI | Update after Level 3 layout is stable. |
| `requirements*.txt` / `pyproject.toml` | Packaging base | Refactor | Editable install works | Environment drift | Add Docker/conda lock path later; keep editable install. |

## 11. What Must Be Upgraded for CCF-B Level 3

Recommended upgrade areas:

1. Research positioning: define DataAudit-LM / URD-Selector with a precise
   problem statement, claim boundary, and evaluation contract.
2. Data: add larger bounded samples, clear license/scope notes, stronger
   dataset registry, and no-fallback enforcement for every Level 3 dataset.
3. Tokenizer: add production-grade BPE/GPT-2-compatible tokenizer path with
   tokenizer manifests.
4. Model scale: run small plus at least one stronger medium/large-lite setting
   under fixed budgets.
5. Baselines: add real C4/Gopher/CCNet-style, neural perplexity, classifier,
   and embedding/diversity baselines.
6. Filter contract: standardize retained corpus manifests, keep-rate controls,
   score distributions, and filter decision logs.
7. Evaluation: add rank stability, Pareto frontier, diversity/risk/cost
   metrics, downstream probes, and mechanism analysis.
8. Statistics: strengthen paired tests and seed/dataset uncertainty reporting.
9. Engineering: add Docker or environment lock, checkpoint manifests, training
   logs, and reproducible rerun commands.
10. Docs: keep the honest negative-result framing while adding a Level 3 upgrade
   roadmap and reviewer-facing limitations.

## 12. Risks Before Refactoring

| Risk | Current severity | Notes |
|---|---|---|
| Legacy-course code dilutes research focus | Medium | Isolate as legacy instead of deleting. |
| Manual result editing risk | Medium | Existing checks help, but registry-to-table immutability should be stronger. |
| Fallback/smoke confusion | Medium | Main evidence is clean; legacy smoke paths must stay labeled. |
| Claim drift during CCF-B upgrade | High | Existing claim contract should be extended before new claims are written. |
| BPE/medium overclaim risk | High | Configs exist but should not be described as completed evidence. |
| No Docker/environment lock | Medium | Editable install works, but reproducibility outside this machine needs stronger environment control. |
| HDQS++ identity risk | Medium | HDQS++ should become historical baseline/failure object, not be deleted. |
| Cross-dataset sample scale | High | OpenWebText/C4 rows are streaming samples only. |

## 13. Immediate Next Step Recommendation

Proceed to Step 1 only after preserving this Step 0 audit snapshot.

Exact next step:

`step1_research_positioning_and_claim_boundary`

Step 1 should define:

- new project name and scope: DataAudit-LM / URD-Selector;
- what remains as historical evidence;
- what becomes legacy;
- what counts as Level 3 evidence;
- forbidden claims for CCF-B/Level 3 wording;
- a migration plan that does not delete current negative results.

Do not start by adding new experiments. Start by freezing the research contract.

## 14. Test Results

Commands run:

```bash
python -m pip install -e .
python -m pytest tests/ -q
python scripts/run_all_checks.py --timeout 300
```

Results:

- Editable install: passed.
- Pytest: `69 passed`.
- Run-all checks: passed.
- Experiment readiness reported: `EXPERIMENT-CANDIDATE`.
- Claim hygiene: passed.
- Main results purity: passed, 24 rows.
- Artifact lineage: passed, 153 registry rows, 42 superseded accepted.
- No-fallback check: passed.
- Split integrity: passed.
- No-test-leakage check: passed.

No minimal compatibility fix was required.

## 15. Changed Files Summary

Files added by this Step 0 audit:

- `docs/repo_audit_before_level3.md`
- `artifacts/reports/step0_readiness_report.json`

Generated verification artifacts updated after adding the new audit report:

- `artifacts/release/claim_hygiene_report.json`
- `artifacts/release/claim_hygiene_report.md`

Protected files intentionally not modified:

- `artifacts/tables/main_results.csv`
- `artifacts/runs/run_registry.jsonl`
- `artifacts/stats/main_results.csv`
- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/experiment_readiness_report.json`
- `README.md`
- `docs/REPORTING_CONTRACT.md`

No experiment result was created, changed, or hand-written in this step.
