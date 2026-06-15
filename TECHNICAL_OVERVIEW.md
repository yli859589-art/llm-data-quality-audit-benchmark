# Technical Overview

The LocalMax release uses GPT-2 token accounting, manifest-backed data preparation, deterministic method outputs, small-model training manifests, clipped-PPL-aware evaluation, statistical summaries, risk/diversity/cost tables, and a LocalMax claim map.

Core scripts:

- `scripts/localmax/make_localmax_release_tables.py`
- `scripts/localmax/make_localmax_release_figures.py`
- `scripts/localmax/finalize_localmax_release.py`
- `scripts/localmax/check_localmax_release_claims.py`
