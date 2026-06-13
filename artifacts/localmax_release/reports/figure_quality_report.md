# LocalMax Figure Quality Report

- Status: `completed`
- Primary metric for result figures: `valid_loss`
- PPL used for comparison: `False`

| Figure | Source Table | Metric | Tie/Label Handling | Forbidden Claims |
|---|---|---|---|---:|
| `claim_boundary_summary.png` | `artifacts/localmax_release/tables/localmax_claim_audit_release.csv` | `release_metadata` | `not_applicable` | `False` |
| `method_ranking_by_valid_loss.png` | `artifacts/localmax_release/tables/localmax_method_summary_release.csv` | `valid_loss` | `ties_marked` | `False` |
| `method_ranking_c4_valid_loss.png` | `artifacts/localmax_release/tables/localmax_method_summary_release.csv` | `valid_loss` | `ties_marked` | `False` |
| `method_ranking_openwebtext_valid_loss.png` | `artifacts/localmax_release/tables/localmax_method_summary_release.csv` | `valid_loss` | `ties_marked` | `False` |
| `risk_diversity_cost_tradeoff.png` | `artifacts/localmax_release/tables/localmax_method_summary_release.csv` | `valid_loss` | `offset_annotations` | `False` |
| `seed_stability_c4_valid_loss.png` | `artifacts/localmax_release/tables/localmax_main_results_release.csv` | `valid_loss` | `dataset_split` | `False` |
| `seed_stability_openwebtext_valid_loss.png` | `artifacts/localmax_release/tables/localmax_main_results_release.csv` | `valid_loss` | `dataset_split` | `False` |
| `seed_stability_valid_loss.png` | `artifacts/localmax_release/tables/localmax_main_results_release.csv` | `valid_loss` | `dataset_split_compat_openwebtext` | `False` |
| `training_strength_summary.png` | `artifacts/localmax_release/tables/localmax_training_summary_release.csv` | `release_metadata` | `normalized_completion_ratio` | `False` |
| `urd_vs_raw_valid_loss_difference.png` | `artifacts/localmax_release/tables/localmax_statistical_summary_release.csv` | `valid_loss` | `not_applicable` | `False` |
| `valid_loss_by_dataset_method.png` | `artifacts/localmax_release/tables/localmax_method_summary_release.csv` | `valid_loss` | `not_applicable` | `False` |
| `valid_loss_by_method.png` | `artifacts/localmax_release/tables/localmax_method_summary_release.csv` | `valid_loss` | `not_applicable` | `False` |

## Superseded Figures

- `artifacts/localmax_release/figures/superseded/method_ranking_by_valid_loss.png`
- `artifacts/localmax_release/figures/superseded/risk_diversity_cost_tradeoff.png`
- `artifacts/localmax_release/figures/superseded/seed_stability_valid_loss.png`
- `artifacts/localmax_release/figures/superseded/training_strength_summary.png`
