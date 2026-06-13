# Project Status

Date: 2026-06-11

## Machine-Readable Status Fields

- historical_release_readiness: `EXPERIMENT-CANDIDATE`
- current_readiness: `LEVEL3_PIPELINE_READY`
- method_status: `honest_audit_framework`
- benchmark_scope_status: `multi_dataset_audit_candidate`
- ccf_c_ready: `false`
- ccf_b_ready: `false`
- level3_pipeline_ready: `true`
- level3_completed_artifact: `false`
- step2_data_source_interface: `implemented`
- step2_smoke_sample_protocol: `available`
- full_100m_or_500m_data_prepared: `false`
- step3_tokenizer_interface: `implemented`
- step3_bpe_smoke_tokenizer: `verified`
- bpe16k_or_bpe32k_mainline_trained: `false`
- level3_tokenizer_matrix_completed: `false`
- step4_filter_interface: `implemented`
- step4_filter_smoke_verification: `available`
- full_strong_baseline_matrix_completed: `false`
- official_c4_gopher_ccnet_reproduced: `false`
- step5_model_training_interface: `implemented`
- step5_tiny_bpe_smoke_training: `verified`
- step5_checkpoint_manifest: `available`
- bpe_mainline_training_completed: `false`
- medium_or_large_lite_training_completed: `false`
- step6_urd_selector_pipeline: `implemented`
- step6_fixed_weight_smoke_selection: `verified`
- step6_pareto_smoke_selection: `verified`
- step6_urd_effectiveness_evidence: `not_established`
- step7_evaluation_v2_infrastructure: `implemented`
- step7_smoke_evaluations: `verified`
- step7_downstream_protocol: `available`
- step7_effectiveness_claim_allowed: `false`
- step8_mechanism_analysis_infrastructure: `implemented`
- step8_smoke_mechanism_diagnostics: `verified`
- step8_protocol_mechanism_analyses: `available`
- step8_full_scale_mechanism_conclusion_allowed: `false`
- step9_artifact_registry_v2: `implemented`
- step9_level3_readiness_gates: `implemented`
- step9_claim_map_level3: `implemented`
- step9_smoke_protocol_main_separation_checks: `implemented`
- main_result_scope: `WikiText-2 official-split small-model matrix`
- cross_dataset_scope: `bounded streaming-sample audit evidence`
- primary_limitation: `method, data scale, model scale, downstream, and mechanism evidence are not yet sufficient for CCF-B`
- recommended_next_step: `step10A_level3_heavy_protocol_freeze`

## Current Result Boundary

Step 2 adds a data-source interface, token-budget sampler, manifest schema, and no-fallback validation. The verified Step 2 output is smoke data only and does not enter `main_results`. FineWeb, Dolma, and Pile are protocol-only or optional until real data is prepared and registered.

Step 3 adds a tokenizer interface, char tokenizer wrapper, BPE smoke tokenizer pipeline, optional GPT-2 wrapper, tokenizer manifests, and tokenizer-specific budget checks. The BPE smoke tokenizer is not mainline model evidence, and BPE16k/BPE32k mainline tokenizer training is not completed.

Step 4 adds a filter interface, filter registry, filter manifests, keep-rate fairness reports, lightweight risk/diversity/cost summaries, and smoke verification outputs. These outputs are interface artifacts only. They are not model-training evidence, not PPL results, and not full strong-baseline matrix completion.

Step 5 adds a tokenizer-aware model training interface, model-config validation, training manifests, metrics, checkpoint manifest support, and a tiny BPE smoke training run. The Step 5 smoke run is engineering evidence only. It is not a new main result, does not update `main_results`, and does not claim completed small/medium/large-lite BPE training.

Step 6 adds the URD-Selector pipeline with utility, risk, diversity, shift, and cost proxy components, fixed-weight selection, Pareto-style smoke selection, and single-component ablation configs. Step 6 does not run model training, does not add PPL/downstream results, and does not establish URD effectiveness.

Step 7 adds the evaluation_v2 infrastructure layer with LM, downstream protocol, risk, diversity, cost, stability/statistics, and Pareto evaluators. Step 7 outputs are smoke/protocol artifacts only. They do not update `main_results` and do not permit an effectiveness claim.

Step 8 adds the analysis_v2 mechanism-analysis infrastructure layer with proxy-utility, overfiltering, diversity-loss, domain-shift, Pareto-mechanism, failure-taxonomy, rank-stability, tokenizer-sensitivity, and scale-trend analyzers. Step 8 outputs are smoke/protocol artifacts only. They do not update `main_results`, do not prove URD effectiveness, and do not permit a full-scale mechanism conclusion.

Step 9 adds Level 3 readiness states, readiness gates, a Level 3 claim map, an artifact registry v2, and checks that separate historical main tables from smoke/protocol artifacts. Step 9 does not add new experiments, does not update `main_results`, does not mark Level 3 completion, and does not permit method-success claims.

- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- Reporting contract: `docs/REPORTING_CONTRACT.md`

The candidate matrix now includes raw, random, dedup, HDQS++ v1, HDQS++ v2, the selected v2 no-token-frequency variant, and HDQS++ v3.

- raw mean PPL: `12.6214`
- selected v2 no-token-frequency mean PPL: `14.2653`
- HDQS++ v3 mean PPL: `13.2341`

The interpretation follows the generated method status report and does not claim supported improvement over raw.

OpenWebText and C4 English evidence uses real HuggingFace streaming samples. These are explicitly bounded streaming samples, not complete upstream corpora. Their evidence is reported in `artifacts/cross_dataset/` and `docs/CROSS_DATASET_AUDIT.md`.

## Current Readiness Interpretation

The repository is an experiment-candidate audit benchmark with Step 9 Level 3 pipeline hygiene in place. It is not CCF-B ready, not CCF-C ready, not publication-ready, and not a completed Level 3 artifact.

Current evidence is useful for:

- WikiText-2 official-split small-model audit comparisons;
- bounded streaming-sample OpenWebText/C4 audit checks;
- showing that heuristic filtering can underperform raw data under fair controls;
- validating the Step 5 training-interface contract with a tiny BPE smoke run;
- validating the Step 6 URD selector-interface contract with smoke filter outputs;
- validating the Step 7 evaluation-interface contract with smoke/protocol outputs;
- validating the Step 8 mechanism-analysis contract with smoke/protocol outputs;
- validating Step 9 artifact registry, readiness gates, claim map, and smoke/protocol separation checks;
- preserving negative evidence and artifact lineage.

Current evidence is not sufficient for:

- a method-success claim over raw;
- not full OpenWebText/C4 claims;
- large-scale LLM pretraining conclusions;
- completed downstream evaluation claims;
- completed URD-Selector claims;
- established URD effectiveness claims;
- full-scale mechanism conclusion claims;
- official downstream completion claims;
- completed BPE16k/BPE32k, medium, or large-lite training claims;
- completed CCF-B/Level 3 claims.
- completed Level 3 heavy evidence claims.

Future publication and reviewer notes are archived under `docs/future_publication_notes/`. They are future publication gap notes, not current release claims.

## Boundary

`method_debug` and filtering-only artifacts remain isolated from `main_results`. V3 ablation rows are model-training diagnostics, not primary method claims.

Canonical reporting documents:

- `docs/REPORTING_CONTRACT.md`
- `docs/reporting_contract_level3.md`
- `docs/claim_boundary.md`
- `docs/level3_upgrade_roadmap.md`
- `docs/level3_route.md`
- `docs/level3_readiness_gates.md`
- `docs/level3_claim_boundary.md`
