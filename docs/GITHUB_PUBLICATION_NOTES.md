# GitHub publication notes

## Source provenance

This public-source snapshot was produced from local branch `audit/final-independent-verification` at `c49133733a8a72f9f0cfdfc55c82a0f71ebeef40`. It contains the audit repairs `7977be9`, `943fe56`, and `fe97f5f`, and the P2-2 acceptance commit `84ac8fd` in its source ancestry.

The GitHub publication branch is deliberately based on the pre-existing remote `main` history and imports this audited source tree in one non-force-pushed commit. The source provenance is retained because the local audit history and the pre-existing public history were unrelated.

## Deliberately excluded material

The public tree does not include raw C4, OpenWebText, WikiText, or other source corpora and dataset splits; large LocalMax/CCFC filtering outputs; binary checkpoints; model weights; caches; temporary test trees; release ZIPs; local credentials; `.env` files; private absolute paths; or generated reports that embed those paths.

These items are unnecessary for source review, too large for a source repository, potentially contain source-text data, or are reproducible from the included code and documented procedures.

## Audit boundary

Nine formally declared C4/OpenWebText shards are unavailable in the source environment. No substitute fixture is presented as a formal corpus, and no claim of completed real-corpus training is made. The complete historical isolated test result was `313 passed, 3 failed`; see the final defect register for the reproducible legacy failure class.
