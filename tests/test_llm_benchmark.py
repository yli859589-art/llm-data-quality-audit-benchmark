import tempfile
import unittest
from pathlib import Path

from course_project_suite.llm_benchmark.attention import benchmark_attention_suite
from course_project_suite.llm_benchmark.dataset import (
    build_ablation_variants,
    inject_web_noise,
    quality_metrics,
)
from course_project_suite.llm_benchmark.reporting import write_bar_chart, write_line_chart


class LlmBenchmarkTests(unittest.TestCase):
    def test_full_pipeline_reduces_duplicates_and_pii(self):
        base = ['A public text document with enough words for quality filtering.'] * 12
        noisy = inject_web_noise(base)
        variants = build_ablation_variants(noisy)
        raw = quality_metrics(variants['raw_noisy_baseline'])
        full = quality_metrics(variants['full_pipeline'])
        self.assertLess(full['duplicate_documents'], raw['duplicate_documents'])
        self.assertEqual(full['email_hits'], 0)
        self.assertEqual(full['phone_hits'], 0)

    def test_attention_suite_matches_naive(self):
        rows = benchmark_attention_suite((8,), heads=1, dim=4, repeats=1)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertLess(row['max_abs_error_vs_naive'], 1e-5)
            self.assertGreater(row['query_tokens_per_second'], 0)

    def test_svg_reporters_write_renderable_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            line = Path(tmp) / 'line.svg'; bars = Path(tmp) / 'bars.svg'
            write_line_chart(line, {'model': [(0, 2.0), (1, 1.0)]}, 'Title', 'x', 'y')
            write_bar_chart(bars, [{'implementation': 'naive', 'sequence_length': 8, 'query_tokens_per_second': 10.0}], 'Title')
            self.assertIn('<svg', line.read_text(encoding='utf-8'))
            self.assertIn('<svg', bars.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
