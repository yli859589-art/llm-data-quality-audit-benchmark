# Claim Hygiene Report

- Status: `passed`
- Scanned files: `54`
- Optional files not present: `0`
- Flagged phrases: `32`
- Unsafe claims: `0`

## Optional Files Not Present

- None

## Flagged Phrases

| File | Line | Phrase | Classification | Reason |
|---|---:|---|---|---|
| `README.md` | 201 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/BENCHMARK_PROTOCOL.md` | 4 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/EXPERIMENT_DASHBOARD.md` | 7 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/EXPERIMENT_READINESS_REPORT.md` | 34 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/FIGURE_INDEX.md` | 4 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/FRESH_CLONE_TEST.md` | 8 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/future_publication_notes/README.md` | 5 | `CCF-C ready` | `archival_context` | Phrase appears in archival or future-publication context. |
| `docs/future_publication_notes/README.md` | 27 | `HDQS++ outperforms raw` | `archival_context` | Phrase appears in archival or future-publication context. |
| `docs/PROJECT_PRESENTATION_NOTES.md` | 44 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/PROJECT_PRESENTATION_NOTES.md` | 44 | `paper-ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/README.md` | 5 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/README.md` | 5 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/README.md` | 66 | `paper-ready` | `archival_context` | Phrase appears in archival or future-publication context. |
| `docs/RELEASE_CHECKLIST.md` | 4 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 26 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 40 | `HDQS++ beats raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 41 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 42 | `HDQS++ improves LLM pretraining` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 43 | `state-of-the-art` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 44 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 45 | `full OpenWebText` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 46 | `full C4` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 48 | `significant improvement over raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 81 | `web-scale result` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `docs/REPORTING_CONTRACT.md` | 102 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `RESUME_BULLETS.md` | 39 | `developed a state-of-the-art filter` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `RESUME_BULLETS.md` | 39 | `state-of-the-art` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `RESUME_BULLETS.md` | 40 | `improved LLM pretraining perplexity` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `RESUME_BULLETS.md` | 41 | `beat raw baseline` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `RESUME_BULLETS.md` | 42 | `CCF-C ready` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `RESUME_BULLETS.md` | 42 | `CCF-C-ready project` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |
| `TECHNICAL_OVERVIEW.md` | 5 | `HDQS++ outperforms raw` | `allowed_negative_context` | Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context. |

## Pass/Fail Rule

The check fails only for `unsafe_claim`. Phrases in explicit forbidden-claim, non-claim, limitation, claim-boundary, or archival contexts are retained as allowed exceptions.
