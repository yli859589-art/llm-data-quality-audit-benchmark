from __future__ import annotations

from dataaudit_lm.data.records import make_record
from dataaudit_lm.filters.reference_lm import FrozenUnigramReferenceLM, apply_reference_lm_filter


def test_reference_lm_scoring_outputs_token_level_nll_and_manifest_fields() -> None:
    records = [
        make_record(
            record_id="a",
            source_row_id="0",
            text="alpha beta alpha",
            source_dataset="toy",
            source_revision="r",
        ),
        make_record(
            record_id="b",
            source_row_id="1",
            text="rare rare token",
            source_dataset="toy",
            source_revision="r",
        ),
    ]
    reference = FrozenUnigramReferenceLM(["alpha beta alpha gamma"])

    result = apply_reference_lm_filter(records, reference_lm=reference, keep_lowest_fraction=0.5)

    assert result.kept_ids == ["a"]
    score = result.manifest["scores"][0]
    assert {
        "document_id",
        "reference_nll",
        "scored_tokens",
        "window_count",
        "score_status",
        "model_revision",
    } <= set(score)
    assert result.manifest["parameters"]["reference_model"] == "FrozenUnigramReferenceLM"
