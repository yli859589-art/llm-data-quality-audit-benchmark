import tempfile
import unittest
from pathlib import Path

from course_project_suite.llm_benchmark.dataset_matrix import (
    benchmark_config_for_dataset,
    dataset_keys_for_mode,
    resolve_dataset_config,
    run_dataset_matrix,
)
from course_project_suite.llm_benchmark.datasets import load_configured_dataset


class DatasetMatrixTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_dataset_keys_by_mode(self):
        self.assertEqual(dataset_keys_for_mode("quick"), ("tiny_shakespeare",))
        self.assertIn("wikitext2", dataset_keys_for_mode("full"))
        with self.assertRaises(ValueError):
            dataset_keys_for_mode("paper")

    def test_unknown_dataset_key_raises(self):
        with self.assertRaises(ValueError):
            resolve_dataset_config("unknown", self.root)

    def test_benchmark_output_path_is_dataset_specific(self):
        loaded = load_configured_dataset(
            self.root / "configs" / "datasets" / "tiny_shakespeare.yaml",
            root=self.root,
        )
        cfg = benchmark_config_for_dataset(
            loaded,
            dataset_key="tiny_shakespeare",
            mode="quick",
            output_dir=Path("artifacts/dataset_matrix"),
        )
        self.assertEqual(
            Path(cfg.output_dir).as_posix(), "artifacts/dataset_matrix/tiny_shakespeare"
        )

    def test_dry_run_writes_summary_and_uses_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = run_dataset_matrix(
                root=self.root,
                output_dir=Path(tmp),
                dataset_keys=("wikitext2",),
                mode="quick",
                allow_network=False,
                dry_run=True,
            )
            self.assertEqual(rows[0].status, "dry_run")
            self.assertTrue(rows[0].used_fallback)
            self.assertTrue((Path(tmp) / "dataset_matrix_summary.csv").exists())
            self.assertTrue((Path(tmp) / "wikitext2").exists())


if __name__ == "__main__":
    unittest.main()
