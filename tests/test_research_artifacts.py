import unittest

from course_project_suite.llm_benchmark.research import (
    build_curriculum_report,
    build_pipeline_order_report,
)


class ResearchArtifactTests(unittest.TestCase):
    def test_curriculum_report_is_deterministic(self):
        docs = [
            "Useful coherent document with several different natural language words.",
            "$$$ template template template <nav>x</nav>",
            "Another useful paragraph with varied vocabulary and stable topic.",
            "footer footer footer footer",
        ]
        first = build_curriculum_report(docs, seed=7)
        second = build_curriculum_report(docs, seed=7)
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first["strategies"]), 6)

    def test_pipeline_order_report_has_required_rows(self):
        docs = [
            "Contact editor@example.org with a coherent document body.",
            "Contact editor@example.org with a coherent document body.",
            "<nav>menu</nav> template template template",
        ]
        report = build_pipeline_order_report(docs)
        names = {row["pipeline_order"] for row in report["rows"]}
        self.assertIn("redact_before_dedup", names)
        self.assertIn("near_dedup_after_hdqs", names)


if __name__ == "__main__":
    unittest.main()
