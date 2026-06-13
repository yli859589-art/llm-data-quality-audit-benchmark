from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path.cwd()


def test_hotfix_figures_are_readability_hardened() -> None:
    report = json.loads((ROOT / "artifacts/localmax_release/reports/figure_quality_report.json").read_text(encoding="utf-8"))

    assert report["figure_readability_hardened"] is True
    figures = {item["figure_name"]: item for item in report["figures"]}
    assert "seed_stability_openwebtext_valid_loss.png" in figures
    assert "seed_stability_c4_valid_loss.png" in figures
    assert figures["seed_stability_openwebtext_valid_loss.png"]["long_axis_label_count"] == 0
    assert figures["seed_stability_c4_valid_loss.png"]["long_axis_label_count"] == 0
    assert figures["training_strength_summary.png"]["tie_handling"] == "normalized_completion_ratio"
    assert figures["method_ranking_c4_valid_loss.png"]["tie_handling"] == "ties_marked"
    assert all(item["metric_used"] in {"valid_loss", "release_metadata"} for item in report["figures"])
    assert not any(item["forbidden_claims_found"] for item in report["figures"])


def test_hotfix_figure_files_are_nonempty_and_reasonably_sized() -> None:
    expected = [
        "seed_stability_openwebtext_valid_loss.png",
        "seed_stability_c4_valid_loss.png",
        "risk_diversity_cost_tradeoff.png",
        "training_strength_summary.png",
        "method_ranking_openwebtext_valid_loss.png",
        "method_ranking_c4_valid_loss.png",
    ]
    for name in expected:
        path = ROOT / "artifacts/localmax_release/figures" / name
        assert path.exists(), name
        assert path.stat().st_size > 1000
        with Image.open(path) as image:
            width, height = image.size
        assert width >= 900
        assert height >= 600

