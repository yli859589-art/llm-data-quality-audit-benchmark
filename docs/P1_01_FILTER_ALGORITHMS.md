# P1-1 Filter Algorithm Upgrade

## Implemented, code-tested changes

- `minhash_near_dedup` is now a deterministic MinHash/LSH implementation with
  configurable shingle size, permutations, bands, threshold and seed. It uses
  LSH only to retrieve candidates and confirms candidates with exact shingle
  Jaccard before removing a document. The lexicographically smallest document
  ID remains the cluster representative, independent of input order.
- The prior proxy configuration is retained as a compatible name, but declares
  the new `minhash_lsh_near_dedup` type. It is not presented as a neural or
  external service.
- Quality profiles now expose empty/control-text status, token count, symbol,
  punctuation and repeated-line ratios, URL/HTML counts, script-level language
  indicators and readability. C4/Gopher proxies include this evidence in their
  decision metadata. These remain transparent heuristics, not official C4 or
  Gopher reproductions.
- URD selection accepts an explicit token budget and maximum risk score. It
  retains ranked documents only while both constraints hold and records
  budget/risk decisions. Utility, risk and diversity remain 0–1 heuristic
  proxies; no improvement in downstream LM performance is claimed.

## Test evidence

`tests/test_p1_filter_algorithms.py` uses labelled fixtures only:

- exact duplicate cluster: representative retained, duplicate removed;
- input reversal: same representative set;
- readable text retained while empty/control text is rejected;
- URD selected tokens never exceed its configured budget.

The P1 test fixtures are not real corpus evidence. They establish algorithmic
behaviour only. Existing filter/URD regression tests were also run without
writing new experiment artifacts.

### Measured fixture-scale performance

On 300 labelled synthetic benchmark documents (32 permutations, 8 bands), the
actual in-process run took 0.082 seconds and made 32,678 candidate comparisons
versus 44,850 all-pairs comparisons. This is only a small fixture baseline; it
does not establish throughput or recall on production corpora.

## Boundaries and P1-2 handoff

The workspace still has 0/3 C4 and 0/6 OpenWebText declared data shards. No
claim is made about filtering quality, false-positive rates, throughput, or
model utility on the missing 200M-token corpus. P1-2 should build shard-level
streaming indexes, disk-backed MinHash buckets, resumable processing,
cross-split duplicate audits and measured CPU/RAM throughput on restored real
data. It must write new versioned outputs rather than change historical tables.
