# Data Quality Interventions for Small-Scale Language Model Pretraining: A Reproducible Benchmark Prototype

## Abstract

Pretraining data quality is often discussed in the context of large web-scale
language models, where the full pipeline is difficult to inspect, reproduce, or
adapt in low-resource research environments. This prototype studies a smaller
but auditable setting: deterministic data-quality interventions for compact
language-model pretraining. The benchmark combines controlled corruption, PII
redaction, exact deduplication, Jaccard and MinHash/LSH near-duplicate
detection, a transparent Heuristic Document Quality Score (HDQS), equal-budget
training ablations, synthetic privacy checks, and script-generated artifacts.
The checked-in quick experiment uses Tiny Shakespeare, one CPU seed, and a
short character-level MiniGPT training run. It verifies that the pipeline is
reproducible and shows a preliminary perplexity improvement for the full
pipeline over a raw noisy baseline, while standalone HDQS filtering is not
treated as a stable performance-improving method. The benchmark is therefore a
research prototype and engineering artifact, not a large-scale LLM conclusion.
Full multi-seed, multi-dataset experiments remain necessary before any
paper-level empirical claim.

## 1. Introduction

Language-model pretraining depends on large collections of text, but the
quality of those collections is rarely a single property. A corpus may contain
duplicated pages, low-information boilerplate, personally identifying strings,
encoding artifacts, generated repetition, template text, or domain-specific
language that is either valuable or harmful depending on the task. In large
industrial systems, these issues are handled by complex data pipelines that are
often distributed, expensive, and only partially documented. For students,
independent researchers, and small labs, reproducing that scale is unrealistic.
However, the underlying research question still matters: what happens when we
apply specific data-quality interventions before pretraining a language model,
and how can we measure the effects without confusing engineering convenience
with empirical proof?

This project takes a deliberately small and inspectable approach. Instead of
claiming to model a production web crawl, it constructs a deterministic stress
test around a public local corpus. The stress test injects controlled families
of corruption, including HTML boilerplate, URL spam, PII-like canaries, exact
duplicates, near duplicates, OCR-like artifacts, mojibake, repeated n-grams,
low-information templates, mixed-language snippets, excessive symbols, and
generated-like repetition. Because the noise is deterministic and seed
controlled, a failed experiment can be debugged at the level of individual
documents. This is a different goal from estimating the natural noise rate of
the web. The benchmark is designed to make pipeline behavior reproducible and
auditable before moving to larger datasets.

Small language models are useful in this setting because they make iteration
cheap. A character-level MiniGPT trained for a short number of steps cannot
establish conclusions about modern large language models, but it can act as a
smoke test for the experimental plumbing. If a pipeline cannot generate
consistent dataset cards, equal-budget comparisons, privacy reports, ablation
tables, training curves, and failure notes in the small setting, it is unlikely
to be trustworthy at larger scale. The quick experiment therefore answers a
narrow question: can the benchmark execute end to end on CPU, preserve artifact
provenance, and expose the difference between raw, partially cleaned, filtered,
and full-pipeline variants?

The central design constraint is fairness of comparison. Data filters change
retention rates, so comparing a raw corpus with a heavily filtered corpus can
mix two effects: document quality and amount of training text. This prototype
therefore trims compared variants to a shared character budget by default.
That choice does not solve every fairness concern, especially for tokenizers
whose token counts differ across text distributions, but it prevents the most
obvious confound in the current character-level quick experiment. The benchmark
also writes a token budget report so future experiments can explicitly opt into
retention-tradeoff studies without accidentally presenting them as strict
equal-budget comparisons.

The project also treats privacy and deduplication as first-class data-quality
components. PII-like canaries are injected synthetically, then used to compute
redaction recall, residual canary counts, and side-effect counts. Exact
deduplication uses stable hashing, while near deduplication includes both a
transparent Jaccard reference and a MinHash/LSH variant intended for larger
matrix runs. The Jaccard method is easier to audit in quick mode; MinHash/LSH
provides a scalable direction for larger corpora, while still verifying
candidate pairs before removal.

The current quick result should be read carefully. The full pipeline shows a
preliminary perplexity improvement over the raw noisy baseline in the
deterministic smoke test, but the standalone HDQS filter is not consistently
better than raw. This matters because a good paper prototype should not hide
negative or ambiguous ablations. In the current interpretation, HDQS is a
transparent pipeline component that works together with cleaning, redaction,
and deduplication; it is not yet demonstrated as a standalone performance
method. That distinction is reflected in the artifact tables, the HDQS sweep
report, and the limitations.

The intended contribution is therefore a reproducible benchmark scaffold: a
small but complete project that can be run locally, audited in GitHub, and
extended to larger data. It is resume-ready as an engineering and research
prototype, but it is not a completed CCF-C paper project and does not claim
official coursework or private-grader completion.

## 2. Related Work

Pretraining data quality has been studied through filtering, deduplication,
toxicity mitigation, personally identifying information removal, domain
balancing, and benchmark-driven data selection. Large language-model reports
often describe multi-stage pipelines that remove low-quality pages, identify
duplicates, filter unsafe content, and mix domains under tuned ratios. This
prototype is inspired by that broad line of work, but it intentionally does not
claim equivalence to production-scale curation. TODO citation: add concrete
references for large pretraining data pipelines and dataset curation papers.

Deduplication is a recurring theme in language-model training because repeated
documents can distort loss, increase memorization risk, and inflate apparent
coverage. Exact deduplication is straightforward but misses lightly edited
copies, boilerplate variants, and generated near-repetition. Jaccard similarity
over word or character shingles is a common transparent baseline, but an
all-pairs implementation scales poorly. MinHash and locality-sensitive hashing
are widely used approximations for retrieving likely near duplicates without
comparing every pair. This repository includes both: a small-corpus Jaccard
reference and a MinHash/LSH variant for larger matrix experiments. TODO
citation: add standard MinHash/LSH and web-deduplication references.

PII redaction and privacy auditing are related but distinct. A regex-based
redactor can remove emails, phone-like strings, and synthetic identifiers, but
that does not prove absence of private information in a real corpus. The
benchmark therefore limits its privacy result to synthetic canaries: it can
validate that injected canaries are removed and that residual counts are zero
in the generated artifact. It cannot make a formal membership-inference,
memorization, or real-world privacy claim. TODO citation: add references for
PII detection, data privacy in language-model corpora, and exposure-style
memorization metrics.

Data filtering methods range from simple heuristics to classifier-based and
language-model-based quality scores. HDQS belongs to the transparent heuristic
family. It combines lexical diversity, character entropy, repetition penalties,
PII density penalties, URL/HTML noise penalties, non-linguistic-symbol
penalties, length priors, and language consistency. This is deliberately
interpretable: every score can be inspected per document. The tradeoff is that
weights and thresholds require validation on separate data before strong
claims. TODO citation: add references for heuristic and learned quality
filtering in pretraining datasets.

Small language-model evaluation is useful for rapid iteration but limited as a
proxy for large-model behavior. A character-level model can expose whether
training code, token budgets, and artifact generation behave as expected, but
its loss curves are noisy and sensitive to short training schedules. The quick
experiment in this repository is therefore closer to an integration test than
a final empirical study. TODO citation: add references for small-scale language
modeling benchmarks and scaling-law cautions.

Efficient attention benchmarks are included only as a supporting systems
measurement. The project compares a naive reference, an online reference, and
PyTorch SDPA using warmup, median, p25, p75, correctness error, environment
metadata, and estimated CPU working-set bytes. PyTorch SDPA is a framework
primitive, not a novel method introduced here. TODO citation: add references
for scaled dot-product attention, memory-efficient attention, and framework
benchmark methodology.

## 3. Method

The benchmark begins from a dataset configuration. Quick mode uses a local
Tiny Shakespeare file with checksum validation. Full matrix mode supports
dataset keys for Tiny Shakespeare, WikiText-2, OpenWebText sample, C4 sample,
and a mixed debug configuration. Optional public datasets require explicit
network permission and the optional Hugging Face `datasets` package. Without
those, the loader falls back to the local debug corpus and records the fallback
in the dataset matrix summary and dataset card.

The controlled corruption module injects deterministic noise families under a
single seed. Each family can be disabled independently. The goal is not to
simulate exact web noise frequencies, but to create a repeatable stress test
with known failure modes. The generated `noise_report.json` records which
families were enabled, how many interventions were injected, and which
synthetic PII canaries were created.

Cleaning and PII redaction are intentionally simple. HTML-like tags and URLs
are normalized by the shared cleaning utilities, while email, phone, and
ID-like canaries are replaced by placeholders. The privacy report computes how
many canary values were present before processing, how many remain after the
full pipeline, recall of canary removal, a precision-style side-effect
indicator, residual counts, and a lightweight exposure-reduction indicator.
The report explicitly states that it is not a formal privacy audit.

Exact deduplication hashes each document. Near deduplication has two modes. The
Jaccard reference computes word-shingle sets and removes a later document when
its similarity to an earlier retained document crosses a threshold. The
MinHash/LSH variant computes deterministic signatures, buckets signature bands,
retrieves candidate representatives, and verifies candidates with exact
Jaccard before removal. The quick experiment uses Jaccard for transparency;
larger experiments can use MinHash/LSH for scalability.

HDQS assigns each document a score in `[0, 1]`. Component scores include
lexical diversity, normalized character entropy, repetition penalty, PII
density penalty, URL/HTML noise penalty, non-linguistic-symbol penalty, length
prior, language consistency, and an optional duplicate-cluster penalty. The
score is a weighted average. Filtering can use a fixed threshold or a top-k
retention ratio. The generated `quality_scores.csv` stores per-document scores
and components, while `hdqs_sweep_report.json` stores threshold and top-k
sweeps. The sweep is used to inspect retention behavior; it is not hard-coded
to force a desired model result.

The model comparison uses equal-budget variants. Raw, rule-filtered,
HDQS-filtered, and full-pipeline corpora are concatenated and trimmed to a
shared character budget. This prevents a heavily filtered variant from being
trained on less text without that fact being recorded. The character-level
MiniGPT reports train loss, validation loss, perplexity, bits per character,
next-character accuracy, throughput, wall time, and optional CUDA peak memory.
Multi-seed summaries report mean and standard deviation when multiple seeds
are run.

The auxiliary attention benchmark generates random query, key, and value
tensors under a seed, measures a naive reference, an online reference, and
PyTorch SDPA, and reports median throughput and interquartile timing. CPU
memory values are algorithmic estimates. CUDA peak memory is reported only
when CUDA is used.

## 4. Experiment Setup

Quick mode is the default acceptance experiment. It uses the local Tiny
Shakespeare corpus, a single seed (`23`), a short CPU training schedule, and no
network downloads. The current quick training configuration is intentionally
small: it exists to verify execution, artifact generation, and result
provenance. The quick artifacts include `results.json`, `dataset_card.json`,
`token_budget_report.json`, `privacy_report.json`, `hdqs_sweep_report.json`,
CSV tables, Markdown tables, and SVG figures.

Full mode is a planned heavier experiment. The maintained entry point is
`scripts/run_dataset_matrix.py --mode full`, which iterates over configured
dataset keys and writes per-dataset artifacts under
`artifacts/dataset_matrix/<dataset_name>/`. Full mode uses seeds `23`, `42`,
and `3407` and a larger training configuration. Optional public datasets are
not downloaded by default; the user must pass `--allow-network`, install
optional dependencies, and review upstream usage terms.

Metrics include retention rate, duplicate removals, PII-like hits before and
after processing, HDQS distribution, validation loss, perplexity, bits per
character, next-character accuracy, tokens per second, wall time, and attention
throughput. Hardware metadata is recorded in `environment.json` and inside the
attention benchmark artifact.

## 5. Preliminary Results

The checked-in quick result is a single-seed CPU smoke test. It should be read
as preliminary. The raw noisy baseline and full pipeline are trained under the
same character budget. In the generated artifact, the full pipeline shows lower
held-out perplexity than the raw noisy baseline, while standalone HDQS
filtering is not consistently better than raw. This supports the narrow claim
that the deterministic pipeline runs reproducibly and that the full
combination of cleaning, redaction, deduplication, and HDQS is promising in the
stress test. It does not prove that HDQS alone improves language modeling, and
it does not prove that the method transfers to large LLM pretraining.

The ablation table is useful precisely because it contains mixed outcomes.
PII redaction removes canaries but does not solve duplication. Exact and near
deduplication reduce repeated documents but may still leave low-quality text.
Rule filtering removes some low-information templates but is too broad for a
strong quality claim. HDQS improves retained document scores but needs
threshold tuning and multi-dataset validation. The full pipeline combines
multiple interventions and is the only variant that removes duplicates and
PII-like hits while improving the preliminary quick perplexity.

## 6. Limitations

Tiny Shakespeare is a compact public debugging corpus, not a production web
crawl. Injected corruption is controlled and useful for reproducibility, but it
does not estimate natural web-noise rates. Quick mode uses one seed and a
short training schedule, so its loss and perplexity values are not stable
paper-level evidence. HDQS weights and thresholds need tuning on a separate
development split. Multi-dataset matrix runs must be completed before any
generalization claim. Synthetic PII canaries validate the redaction path but
do not constitute a real-world privacy audit. CPU attention measurements are
hardware dependent and report estimated working-set bytes rather than measured
peak memory unless CUDA is used.

## 7. Reproducibility Checklist

Primary quick commands:

```bash
python scripts/check_repo.py
python scripts/run_quick_experiment.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/check_artifacts.py
python -m unittest discover -s tests -v
python scripts/run_coverage.py
ruff check .
mypy src/course_project_suite/llm_benchmark
```

Default quick seed: `23`. Full planned seeds: `23`, `42`, and `3407`.
Expected quick runtime is intended to be CPU friendly. Generated artifacts are
under `artifacts/quick_experiment/`. Dataset-matrix artifacts are under
`artifacts/dataset_matrix/`. Every result table should be regenerated from
machine-readable JSON/CSV artifacts rather than edited by hand.

## 8. Future Work

Future work should run the full multi-dataset matrix with explicit network
permission, add BPE MiniGPT comparisons, tune HDQS weights on held-out
development data, evaluate MinHash/LSH at larger scale, introduce real sampled
web-noise annotations, run significance tests or bootstrap intervals, expand
failure-case analysis, and study language/domain bias introduced by filtering.
Only after those experiments should the project be considered a mature
paper-submission candidate.
