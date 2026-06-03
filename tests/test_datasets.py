import sys
import tempfile
import types
import unittest
from pathlib import Path

from course_project_suite.llm_benchmark.config import load_yaml_config
from course_project_suite.llm_benchmark.dataset import build_dataset_card, chunk_documents
from course_project_suite.llm_benchmark.datasets import load_configured_dataset
from course_project_suite.llm_benchmark.dedup import exact_deduplicate, near_deduplicate


class DatasetConfigTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_tiny_shakespeare_local_config_loads(self):
        loaded = load_configured_dataset(
            self.root / "configs" / "datasets" / "tiny_shakespeare.yaml",
            root=self.root,
        )
        self.assertEqual(loaded.source.dataset_name, "tiny_shakespeare")
        self.assertFalse(loaded.used_fallback)
        self.assertGreater(len(loaded.text), 1_000_000)

    def test_offline_huggingface_config_falls_back(self):
        loaded = load_configured_dataset(
            self.root / "configs" / "datasets" / "openwebtext_sample.yaml",
            root=self.root,
            allow_network=False,
        )
        self.assertTrue(loaded.used_fallback)
        self.assertEqual(loaded.source.dataset_name, "tiny_shakespeare")

    def test_unknown_provider_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text('{"provider":"mystery","dataset_name":"x"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_configured_dataset(path, root=self.root)

    def test_missing_local_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "missing.yaml"
            path.write_text(
                '{"provider":"local","dataset_name":"local","local_path":"missing.txt",'
                '"source":"unit","license_or_usage_note":"unit"}',
                encoding="utf-8",
            )
            with self.assertRaises(FileNotFoundError):
                load_configured_dataset(path, root=root)

    def test_local_non_tiny_config_loads_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.txt").write_text("small local text", encoding="utf-8")
            path = root / "local.yaml"
            path.write_text(
                '{"provider":"local","dataset_name":"unit_local","local_path":"sample.txt",'
                '"source":"unit","license_or_usage_note":"unit"}',
                encoding="utf-8",
            )
            loaded = load_configured_dataset(path, root=root)
            self.assertEqual(loaded.text, "small local text")
            self.assertEqual(loaded.source.path, "sample.txt")

    def test_fake_huggingface_streaming_loader(self):
        fake = types.ModuleType("datasets")

        def load_dataset(*args, **kwargs):
            self.assertEqual(args[0], "fake/path")
            self.assertTrue(kwargs["streaming"])
            return [{"text": "alpha"}, {"text": "beta"}, {"text": ""}]

        fake.load_dataset = load_dataset
        previous = sys.modules.get("datasets")
        sys.modules["datasets"] = fake
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / "hf.yaml"
                path.write_text(
                    '{"provider":"huggingface","dataset_name":"fake","hf_path":"fake/path",'
                    '"split":"train","text_field":"text","sample_documents":3,'
                    '"source":"fake","license_or_usage_note":"unit"}',
                    encoding="utf-8",
                )
                loaded = load_configured_dataset(path, root=root, allow_network=True)
        finally:
            if previous is None:
                sys.modules.pop("datasets", None)
            else:
                sys.modules["datasets"] = previous
        self.assertEqual(loaded.text, "alpha\n\nbeta")
        self.assertFalse(loaded.used_fallback)
        self.assertEqual(loaded.source.dataset_name, "fake")

    def test_invalid_config_parse_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("not: json: compatible", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_yaml_config(path)

    def test_experiment_config_fields_parse(self):
        quick = load_yaml_config(self.root / "configs" / "experiments" / "quick.yaml")
        full = load_yaml_config(self.root / "configs" / "experiments" / "full.yaml")
        self.assertTrue(quick["equal_character_budget"])
        self.assertEqual(quick["seeds"], [23])
        self.assertEqual(full["seeds"], [23, 42, 3407])

    def test_dataset_card_fields_are_complete(self):
        loaded = load_configured_dataset(
            self.root / "configs" / "datasets" / "tiny_shakespeare.yaml",
            root=self.root,
        )
        docs = chunk_documents(loaded.text, max_documents=8)
        exact = exact_deduplicate(docs + docs[:2])
        near = near_deduplicate(exact.documents)
        card = build_dataset_card(
            loaded.source,
            raw_documents=docs + docs[:2],
            retained_documents=near.documents,
            random_seed=23,
            exact_removed=exact.removed,
            near_removed=near.removed,
        )
        for field in [
            "dataset_name",
            "source",
            "license_or_usage_note",
            "split",
            "raw_chars",
            "retained_chars",
            "retention_rate",
            "num_docs",
            "num_duplicates_removed",
            "num_near_duplicates_removed",
            "pii_count_before",
            "pii_count_after",
            "random_seed",
            "created_at",
            "code_version/git_commit",
        ]:
            self.assertIn(field, card)


if __name__ == "__main__":
    unittest.main()
