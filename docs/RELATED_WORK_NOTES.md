# Related Work Notes

## Data Quality and Web Corpora

Large language models depend on heavy corpus filtering, deduplication, and
mixture design. C4, Gopher, The Pile, RefinedWeb, and Dolma show that data
provenance and filtering choices materially affect downstream behavior. This
project borrows the review lens, not the scale: every data decision is meant
to produce an auditable artifact.

## Deduplication and Memorization

Document resemblance, exact hashing, MinHash-style similarity, and training
data extraction studies motivate treating deduplication and privacy as linked
concerns. The repository implements exact, Jaccard, and MinHash-LSH variants
and records synthetic PII canary removal, but it does not claim a formal
privacy guarantee.

## Scaling and Compute Budgets

Scaling-law and compute-optimal training papers motivate reporting model size,
token budget, seed count, and compute context. The new model-card script
records approximate model size; future paper runs need measured training logs.

## Tokenization and Curriculum

BPE, SentencePiece, and curriculum-learning work motivate controlled tokenizer
and data-order experiments. Current MiniGPT/BPE demos are infrastructure
evidence; they need real validation curves before supporting paper claims.
