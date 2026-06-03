# Error Analysis

Mode: `quick`
Seed setting: `23`
Training budget: `18000` characters per compared variant.
Interpretation: this file records known failure boundaries from the current compact run.
Limitation note: larger datasets and human-reviewed categories are required before paper-level error analysis.

Removed documents: `44`

Known quick-mode failure boundaries:

- Some useful but short text can receive a low length-prior score.
- Standalone HDQS can underperform the raw baseline in compact runs.
- Synthetic web noise is a reproducible stress test, not a natural-noise estimate.
