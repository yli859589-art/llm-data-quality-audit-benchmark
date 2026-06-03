import tempfile
import unittest
from pathlib import Path

from scripts.clean_artifacts import clean_generated_paths


class CleanArtifactsTests(unittest.TestCase):
    def test_clean_removes_caches_without_deleting_official_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "pkg" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "module.pyc").write_bytes(b"cache")
            (root / ".coverage").write_text("coverage", encoding="utf-8")
            official = root / "artifacts" / "quick_experiment"
            official.mkdir(parents=True)
            (official / "results.json").write_text("{}", encoding="utf-8")

            removed = clean_generated_paths(root)

            self.assertIn(".coverage", removed)
            self.assertFalse(cache.exists())
            self.assertTrue((official / "results.json").exists())

    def test_dry_run_keeps_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / ".pytest_cache"
            cache.mkdir()
            removed = clean_generated_paths(root, dry_run=True)
            self.assertEqual(removed, [".pytest_cache"])
            self.assertTrue(cache.exists())


if __name__ == "__main__":
    unittest.main()
