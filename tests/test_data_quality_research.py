import unittest
from dataclasses import replace
from pathlib import Path

from course_project_suite.llm_benchmark.dataset import enforce_equal_character_budget
from course_project_suite.llm_benchmark.datasets import load_configured_dataset
from course_project_suite.llm_benchmark.dedup import (
    exact_deduplicate,
    jaccard_similarity,
    near_deduplicate,
)
from course_project_suite.llm_benchmark.noise import NoiseConfig, inject_controlled_noise
from course_project_suite.llm_benchmark.privacy import evaluate_synthetic_canaries
from course_project_suite.llm_benchmark.quality import filter_by_quality, score_document
from course_project_suite.llm_benchmark.statistics import summarize


class DataQualityResearchTests(unittest.TestCase):
    def test_noise_injection_is_seed_controlled_and_toggleable(self):
        documents = ["A clean source document with enough useful words."] * 10
        disabled = NoiseConfig(
            html_boilerplate=False,
            url_spam=False,
            pii_canaries=False,
            exact_duplicates=False,
            near_duplicates=False,
            ocr_corruption=False,
            mojibake=False,
            repeated_ngrams=False,
            low_information_templates=False,
            mixed_language=False,
            excessive_symbols=False,
            generated_repetition=False,
        )
        self.assertEqual(inject_controlled_noise(documents, disabled).documents, documents)
        enabled = replace(disabled, pii_canaries=True)
        first = inject_controlled_noise(documents, enabled)
        second = inject_controlled_noise(documents, enabled)
        self.assertEqual(first.documents, second.documents)
        self.assertGreater(first.report["injected_counts"]["pii_canaries"], 0)

    def test_hdqs_scores_clean_document_above_repetition(self):
        clean = (
            "A carefully edited paragraph presents a coherent argument with varied "
            "language and enough detail for a small language-model experiment."
        )
        noisy = "!!! template template template template $$$ https://spam.invalid <nav>x</nav>"
        clean_score, _ = score_document(clean)
        noisy_score, _ = score_document(noisy)
        self.assertGreater(clean_score, noisy_score)
        retained, _ = filter_by_quality([clean, noisy], threshold=(clean_score + noisy_score) / 2)
        self.assertEqual(retained, [clean])

    def test_exact_and_near_dedup_keep_different_documents(self):
        base = "alpha beta gamma delta epsilon zeta eta theta"
        near = base + " updated"
        different = "completely unrelated prose about another subject entirely"
        exact_result = exact_deduplicate([base, base, different])
        self.assertEqual(exact_result.removed, 1)
        near_result = near_deduplicate([base, near, different], threshold=0.7)
        self.assertEqual(near_result.documents, [base, different])
        self.assertGreater(jaccard_similarity(base, near), 0.7)

    def test_equal_character_budget_is_strict(self):
        inputs = {"raw": ["a" * 100], "filtered": ["b" * 70]}
        trimmed, report = enforce_equal_character_budget(inputs, requested_chars=90)
        self.assertEqual({len(value) for value in trimmed.values()}, {70})
        self.assertEqual(report["shared_character_budget"], 70)

    def test_optional_dataset_uses_offline_fallback(self):
        root = Path(__file__).resolve().parents[1]
        loaded = load_configured_dataset(
            root / "configs" / "datasets" / "wikitext2.yaml",
            root=root,
            allow_network=False,
        )
        self.assertTrue(loaded.used_fallback)
        self.assertEqual(loaded.source.dataset_name, "tiny_shakespeare")

    def test_privacy_report_counts_synthetic_canary_removal(self):
        canaries = [
            {
                "email": "editor@example.org",
                "phone": "+1 412 555 1000",
                "id_like": "ID-17-0000",
            }
        ]
        report = evaluate_synthetic_canaries(
            ["Contact editor@example.org or +1 412 555 1000; ID-17-0000."],
            ["Contact <EMAIL> or <PHONE>; <ID>."],
            canaries,
        )
        self.assertEqual(report["residual_canary_values_after_processing"], 0)
        self.assertEqual(report["synthetic_canary_removal_recall"], 1.0)

    def test_statistics_reports_single_seed_boundary(self):
        summary = summarize([3.0])
        self.assertEqual(summary["std"], 0.0)
        self.assertIsNone(summary["ci95_low"])


if __name__ == "__main__":
    unittest.main()
