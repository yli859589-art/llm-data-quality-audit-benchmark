# DataAudit-LM Evidence Scope

The current repository contains reusable local evidence for auditing
pretraining-data filters. It does not promote unfinished experiments to
completed results.

Completed evidence:

- 2 real data sources
- 7 filtering methods
- 3 seeds
- 42 controlled training runs
- Per-token language-model metric audit
- Local downstream probe rows
- Artifact integrity and document consistency checks

Known gaps:

- The planned final matrix is 2 datasets x 6-8 independent methods x at least 5 seeds.
- The current downstream probe is local and diagnostic.
- The reference-model filtering path needs a separate implementation audit.
- The raw duplicate-retention policy needs a dedicated ingestion audit before
  stronger exact-dedup conclusions are made.
