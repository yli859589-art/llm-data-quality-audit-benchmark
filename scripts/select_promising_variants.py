from __future__ import annotations

from experiment_utils import root
from analysis.variant_selection import select_variants, write_variant_outputs


def main() -> None:
    selection = select_variants(
        ablation_path=root / "artifacts" / "ablations" / "model_training_ablation_results.csv",
        method_comparison_path=root / "artifacts" / "stats" / "method_comparison_summary.csv",
        diagnostics_path=root / "artifacts" / "diagnostics" / "hdqspp_failure_analysis.csv",
        method_debug_path=root / "artifacts" / "method_debug" / "method_debug_results.csv",
        main_results_path=root / "artifacts" / "tables" / "main_results.csv",
        stats_main_path=root / "artifacts" / "stats" / "main_results.csv",
    )
    write_variant_outputs(selection, output_dir=root / "artifacts" / "methods")
    promoted = [
        row["variant_name"]
        for row in selection["rows"]
        if row["decision"] == "promote_to_3seed"
    ]
    print(f"Promising variant rows: {len(selection['rows'])}")
    print(f"Promoted variants: {', '.join(promoted) if promoted else 'none'}")


if __name__ == "__main__":
    main()
