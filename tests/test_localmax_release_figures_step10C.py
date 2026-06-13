from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_release_figures_exist_or_are_reported() -> None:
    manifest = json.loads((ROOT / "artifacts/localmax_release/figures/figure_manifest.json").read_text(encoding="utf-8"))
    expected = {
        "valid_loss_by_method.png",
        "valid_loss_by_dataset_method.png",
        "urd_vs_raw_valid_loss_difference.png",
        "seed_stability_valid_loss.png",
        "risk_diversity_cost_tradeoff.png",
        "method_ranking_by_valid_loss.png",
        "training_strength_summary.png",
        "claim_boundary_summary.png",
    }
    generated = {Path(path).name for path in manifest["generated_figures"]}

    assert expected <= generated
    assert manifest["primary_metric"] == "valid_loss"
    assert manifest["ppl_used_for_method_comparison"] is False
    for name in expected:
        path = ROOT / "artifacts/localmax_release/figures" / name
        assert path.exists()
        assert path.stat().st_size > 1000

