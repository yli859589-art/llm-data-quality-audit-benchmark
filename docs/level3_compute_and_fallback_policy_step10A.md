# Level 3 Compute and Fallback Policy Step 10A

The Level 3 route requires substantial storage, GPU time, and CPU data
processing. Step 10A records those expectations without executing the heavy
jobs.

## Expected Resources

- Multi-TB storage for corpora, filtered corpora, checkpoints, and artifacts.
- Multi-day GPU time depending on scale.
- Dedicated GPU resources for medium and selected large-lite runs.
- High-throughput CPU workers for data preparation and filtering.

## Fallback Rules

- 1B tokens can fall back to 500M tokens if all minimum thresholds still hold.
- 500M tokens falling to 100M tokens downgrades the artifact to Level 2 or
  incomplete.
- Four datasets can fall back to three datasets and remain at the minimum floor.
- Full large-lite can fall back to selected large-lite only with an exploratory
  label.
- Official CCNet can fall back to a CCNet proxy only when the proxy boundary is
  explicit.
- Official downstream falling to a subset blocks completed Level 3 claims.

