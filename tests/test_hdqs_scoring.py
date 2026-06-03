import unittest

from course_project_suite.llm_benchmark.experiment import _build_hdqs_sweep_report
from course_project_suite.llm_benchmark.quality import filter_by_quality, score_document


class HdqsScoringTests(unittest.TestCase):
    def test_clean_document_scores_above_obvious_noise(self):
        clean = (
            "A coherent paragraph contains varied terms, a stable topic, and enough length "
            "to resemble useful training text for a small language model."
        )
        noise = "$$$ !!! template template template https://spam.invalid <div>nav</div>"
        self.assertGreater(score_document(clean)[0], score_document(noise)[0])

    def test_top_k_retention_keeps_requested_fraction(self):
        docs = [
            "useful natural language document with varied words and context",
            "another coherent document with enough lexical diversity to keep",
            "$$$ !!! template template template",
            "footer footer footer footer footer",
        ]
        retained, scores = filter_by_quality(docs, retention_ratio=0.5)
        self.assertEqual(len(retained), 2)
        self.assertEqual(len(scores), 4)

    def test_sweep_report_contains_threshold_and_top_k_rows(self):
        docs = [
            "useful natural language document with varied words and context",
            "$$$ !!! template template template",
            "another coherent document with enough lexical diversity to keep",
        ]
        report = _build_hdqs_sweep_report(docs, raw_perplexity=10.0, hdqs_perplexity=11.0)
        self.assertEqual(
            report["standalone_hdqs_status"],
            "standalone_hdqs_not_better_than_raw_in_this_quick_run",
        )
        self.assertGreater(len(report["threshold_rows"]), 3)
        self.assertEqual(len(report["top_k_rows"]), 3)


if __name__ == "__main__":
    unittest.main()
