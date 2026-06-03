import unittest

from course_project_suite.llm_benchmark.statistics import (
    aggregate_model_runs,
    bootstrap_mean_ci,
    paired_difference_summary,
)


class StatisticsTests(unittest.TestCase):
    def test_bootstrap_ci_and_paired_difference(self):
        ci = bootstrap_mean_ci([1.0, 2.0, 3.0], samples=20, seed=1)
        self.assertEqual(ci["count"], 3)
        diff = paired_difference_summary([3.0, 4.0], [2.5, 3.0])
        self.assertTrue(diff["positive_mean_improvement"])

    def test_aggregate_model_runs_outputs_tables_and_tests(self):
        runs = []
        for seed in [23, 42]:
            runs.append(
                {
                    "variant": "raw_noisy_baseline",
                    "seed": seed,
                    "final_val_perplexity": 10.0 + seed / 1000,
                    "final_val_loss": 2.0,
                    "final_val_next_char_accuracy": 0.2,
                }
            )
            runs.append(
                {
                    "variant": "full_pipeline",
                    "seed": seed,
                    "final_val_perplexity": 9.0 + seed / 1000,
                    "final_val_loss": 1.9,
                    "final_val_next_char_accuracy": 0.25,
                }
            )
        seed_rows, aggregate_rows, tests = aggregate_model_runs(runs)
        self.assertEqual(len(seed_rows), 4)
        self.assertEqual(len(aggregate_rows), 2)
        self.assertIn("raw_noisy_baseline_vs_full_pipeline", tests["paired"])
        self.assertEqual(
            tests["paired"]["raw_noisy_baseline_vs_hdqs_filter"]["status"],
            "skipped_missing_variant",
        )


if __name__ == "__main__":
    unittest.main()
