# Filter Pipeline Step 4

## Purpose

Step 4 upgrades only the baseline/filter layer. It adds a unified filter
interface, filter manifests, decision logs, keep-rate reports, lightweight
risk/diversity/cost summaries, and smoke verification on Step 2 data.

Step 4 does not run language-model training, does not add PPL results, does not
add downstream evaluation, and does not modify any canonical main-result table.

## Existing Baselines to Preserve

The repository already has useful baseline/filter assets:

- `raw`
- `random_same_keep_rate`
- `dedup_only` / exact deduplication
- `length_filter`
- HDQS++ v1/v2/v3
- earlier C4/Gopher-style heuristic artifacts
- earlier n-gram perplexity-quality proxy artifacts
- failure diagnostics and negative-result evidence

These assets are retained. They are not deleted, rewritten as wins, or rerun as
main experiments in Step 4.

## Why Raw and Dedup Are Strong Baselines

Raw data is the keep-all reference. In small controlled data-filtering studies,
raw is often hard to beat because filtering can remove useful lexical coverage,
domain coverage, or rare examples.

Exact deduplication is also a strong baseline because it removes repeated
documents without using a fragile quality proxy. It is simple, auditable, and
usually easier to interpret than a learned or heuristic quality score.

## HDQS++ Status

HDQS++ is preserved as a historical baseline and failure-analysis object. Step 4
does not delete HDQS++ and does not claim HDQS++ succeeds over raw. The wrapper
labels HDQS++ as historical evidence so future work can compare against it
without losing the negative result.

## New Filter Interface

Step 4 adds `src/filters_v2/` with:

- `FilterConfig`
- `FilterInput`
- `FilterDecision`
- `FilterResult`
- `BaseFilter`
- filter registry
- JSONL IO helpers
- manifest validation
- keep-rate utilities
- lightweight risk/diversity/cost summaries

Each filter produces:

- `selected_doc_ids.jsonl`
- `decisions.jsonl`
- `scores.jsonl`
- `filter_manifest.json`
- `keep_rate_report.json`
- `risk_report.json`
- `diversity_report.json`
- `cost_report.json`

## Filter Manifest Schema

Step 4 manifests use:

`manifest_version = step4.filter_manifest.v1`

Required fields include filter identity, dataset manifest path/hash, tokenizer
manifest path/hash, target keep-rate, actual document keep-rate, actual token
keep-rate, input and kept document/token counts, seed, proxy status, external
dependency status, smoke status, output hashes, and notes.

All output hashes are real file hashes. Manifest validation checks output file
existence, output hashes, dataset manifest hash, tokenizer manifest hash,
smoke-only status, proxy flags, and keep-rate fields.

## Keep-Rate Fairness Policy

Step 4 records both document keep-rate and token keep-rate. Future training
fairness must not rely only on document keep-rate because different tokenizers
or filters can change token counts even when document counts look similar.

When a target keep-rate cannot be matched exactly because of integer document
counts, the keep-rate report records that reason.

## Token Keep-Rate vs Document Keep-Rate

Document keep-rate answers: how many records were kept?

Token keep-rate answers: how much estimated text budget was kept?

Both are needed before future model training can be called fair. Step 4 uses the
Step 2 whitespace proxy token counter for smoke outputs and labels it as such.

## Proxy Baseline Policy

Proxy filters are useful for interface and failure-mode testing, but they are
not official reproductions. Step 4 proxy outputs always set `proxy_used: true`.

The following are proxy/protocol only in Step 4:

- C4-style heuristic proxy
- Gopher-style heuristic proxy
- CCNet-style proxy/protocol
- unigram perplexity proxy
- classifier quality proxy/protocol
- token-set embedding diversity proxy
- lightweight near-dedup proxy when full MinHash is not used

## External Dependency Policy

Filters that would normally require external systems, such as CCNet language ID,
trained classifiers, neural embedding models, or neural LM perplexity models,
must not pretend those systems ran. Step 4 records unavailable external
dependencies and uses deterministic offline proxies only when `--allow-proxy`
is supplied.

## C4 / Gopher / CCNet Boundary

C4-style and Gopher-style filters are transparent heuristic proxies. They check
signals such as length, symbol ratio, URL/HTML noise, repetition, stopword
ratio, and language-text ratio.

CCNet-style filtering is a protocol/proxy with language-confidence and quality
heuristics. It is not full CCNet.

## Perplexity / Classifier / Embedding-Diversity Boundary

The perplexity proxy uses a lightweight unigram inverse-surprisal signal. It is
not neural LM perplexity.

The classifier proxy is a deterministic quality score. It is not a trained
classifier baseline.

The embedding-diversity proxy uses token-set diversity. It is not a neural
embedding model.

## What Step 4 Actually Ran

Step 4 generated smoke filter outputs for:

- `raw`
- `random_same_keep_rate`
- `exact_dedup`
- `length_filter`
- `c4_style_proxy`
- `gopher_style_proxy`
- `perplexity_proxy`
- `embedding_diversity_proxy`

All Step 4 smoke outputs are under:

`artifacts/filter_outputs_step4/wikitext2_smoke/`

They are smoke verification artifacts only.

## What Step 4 Did Not Run

Step 4 did not run model training, PPL evaluation, downstream evaluation,
URD-Selector, neural perplexity filtering, trained classifier filtering, neural
embedding filtering, and it is not full C4, Gopher, or CCNet reproduction
evidence.

Step 4 did not modify:

- `artifacts/tables/main_results.csv`
- `artifacts/stats/main_results.csv`
- `artifacts/cross_dataset/cross_dataset_results.csv`

## Why Step 4 Is Not a Strong-Baseline Result

Step 4 makes baseline/filter outputs uniform and checkable. It does not prove
that the strong baseline matrix improves model quality. That evidence requires
future Step 5 training manifests, controlled model runs, and later evaluation.

## Next Step

The next step is Step 5: model training pipeline upgrade. Step 5 should stabilize
training manifests, checkpoint manifests, loss curves, multi-seed training
protocols, runtime/cost logging, and tokenizer-specific budget controls before
URD-Selector is implemented.
