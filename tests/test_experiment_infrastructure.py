import csv
import tempfile
import unittest
from pathlib import Path

from baselines.data_quality_baselines import run_baseline
from course_project_suite.llm_benchmark.config import load_yaml_config
from data.dataset_manifest import write_dataset_manifest
from data.real_corpora import load_documents_from_config
from data.splitter import deterministic_split
from scoring.hdqs_freeze import build_frozen_protocol
from stats.significance import analyze_registry


class ExperimentInfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_smoke_config_uses_labeled_offline_fallback(self):
        loaded = load_documents_from_config(
            self.root / "configs" / "data" / "wikitext2_smoke.yaml",
            root=self.root,
        )
        self.assertTrue(loaded.metadata["used_fallback"])
        self.assertTrue(loaded.metadata["is_smoke"])
        self.assertIn("local fixture", loaded.metadata["fallback_reason"])

    def test_paper_data_configs_disallow_fallback(self):
        for path in (self.root / "configs" / "data").glob("*_paper.yaml"):
            config = load_yaml_config(path)
            self.assertFalse(config["allow_fallback"])
            self.assertTrue(config["required_real_data"])
            self.assertFalse(config["is_smoke"])

    def test_dataset_manifest_records_hashes_and_splits(self):
        documents = ["alpha beta gamma", "delta epsilon", "zeta eta theta"]
        splits = deterministic_split(documents, seed=7)
        with tempfile.TemporaryDirectory() as tmp:
            manifest = write_dataset_manifest(
                root=self.root,
                dataset_key="unit",
                documents=documents,
                splits=splits,
                metadata={
                    "provider": "unit",
                    "source": "unit",
                    "dataset_name": "unit",
                    "seed": 7,
                },
                output_dir=Path(tmp),
            )
            self.assertEqual(manifest["document_count"], 3)
            self.assertEqual(len(manifest["document_hashes"]), 3)
            self.assertTrue((Path(tmp) / "data_manifest.csv").exists())

    def test_baselines_return_comparable_metrics(self):
        documents = [
            "clean alpha beta gamma delta",
            "clean alpha beta gamma delta",
            "!!! spam https://example.invalid <nav> buy buy buy",
        ]
        retained, result = run_baseline("dedup_only", documents, target_keep_rate=0.5)
        self.assertEqual(result.removed_duplicates, 1)
        self.assertEqual(len(retained), 2)
        random_retained, random_result = run_baseline(
            "random_same_keep_rate",
            documents,
            target_keep_rate=0.5,
            seed=3,
        )
        self.assertEqual(len(random_retained), random_result.output_documents)
        self.assertLess(random_result.retention_rate, 1.0)

    def test_frozen_protocol_records_no_test_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            protocol = build_frozen_protocol(
                dataset_key="unit",
                documents=["a b c", "d e f", "g h i", "j k l"],
                seed=11,
                output_path=Path(tmp) / "frozen.json",
            )
            self.assertTrue(protocol["no_test_leakage"])
            self.assertTrue(protocol["config_sha256"])
            self.assertIn("test", protocol["split_hashes"])

    def test_significance_marks_single_seed_as_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "registry.csv"
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["dataset_key", "baseline_name", "retention_rate"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "dataset_key": "unit",
                        "baseline_name": "raw",
                        "retention_rate": "1.0",
                    }
                )
            result = analyze_registry(registry, Path(tmp) / "stats")
            self.assertEqual(result["summaries"][0]["claim_status"], "unsupported_seed_count")
            self.assertTrue((Path(tmp) / "stats" / "claim_safety_report.md").exists())


if __name__ == "__main__":
    unittest.main()
