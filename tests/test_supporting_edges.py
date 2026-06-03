import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest import mock

import numpy as np

from course_project_suite import run_all as run_all_module
from course_project_suite.cs224n.parser import PartialParse, minibatch_parse
from course_project_suite.cs231n.sequence import (
    attention_forward,
    rnn_step_forward,
    temporal_softmax_loss,
)


class SupportingEdgeTests(unittest.TestCase):
    def test_run_all_result_shape_and_failure(self):
        ok = SimpleNamespace(ok=True, name="ok", metrics={}, to_dict=lambda: {"ok": True})
        fail = SimpleNamespace(ok=False, name="fail", metrics={}, to_dict=lambda: {"ok": False})
        with mock.patch.object(run_all_module, "RUNNERS", [lambda: ok, lambda: fail]):
            results = run_all_module.run_all()
        self.assertEqual([row.ok for row in results], [True, False])

    def test_run_all_json_output_is_stable(self):
        ok = SimpleNamespace(ok=True, name="ok", metrics={}, to_dict=lambda: {"ok": True})
        with (
            mock.patch.object(run_all_module, "RUNNERS", [lambda: ok]),
            mock.patch("sys.argv", ["prog", "--json"]),
            self.assertRaises(SystemExit) as raised,
        ):
            stream = io.StringIO()
            with redirect_stdout(stream):
                run_all_module.main()
        self.assertEqual(raised.exception.code, 0)
        payload = json.loads(stream.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["project_families"], 1)

    def test_parser_empty_and_single_word_boundaries(self):
        parse = PartialParse([])
        self.assertEqual(parse.parse([]), [])
        with self.assertRaises(ValueError):
            parse.parse_step("S")
        single = PartialParse(["word"])
        self.assertEqual(single.parse(["S", "RA"]), [("ROOT", "word")])

    def test_minibatch_parse_simple_dependencies(self):
        class RightArcModel:
            def predict(self, parses):
                return ["S" if item.buffer else "RA" for item in parses]

        self.assertEqual(
            minibatch_parse([["x"], ["y"]], RightArcModel()), [[("ROOT", "x")], [("ROOT", "y")]]
        )

    def test_sequence_attention_mask_and_rnn_shapes(self):
        q = np.array([[[1.0, 0.0], [0.0, 1.0]]])
        k = q.copy()
        v = np.array([[[1.0, 2.0], [3.0, 4.0]]])
        mask = np.array([[[True, False], [True, True]]])
        out, weights = attention_forward(q, k, v, mask)
        self.assertEqual(out.shape, q.shape)
        self.assertAlmostEqual(weights[0, 0, 1], 0.0)
        x = np.ones((2, 3))
        prev = np.zeros((2, 4))
        Wx = np.ones((3, 4)) * 0.1
        Wh = np.ones((4, 4)) * 0.1
        b = np.zeros(4)
        next_h, _ = rnn_step_forward(x, prev, Wx, Wh, b)
        self.assertEqual(next_h.shape, (2, 4))
        self.assertTrue(np.all(np.isfinite(next_h)))

    def test_temporal_softmax_loss_masks_padding(self):
        scores = np.zeros((2, 3, 4))
        labels = np.array([[0, 1, 2], [1, 2, 3]])
        mask = np.array([[1, 1, 0], [1, 0, 0]], dtype=float)
        loss, dx = temporal_softmax_loss(scores, labels, mask)
        self.assertGreater(loss, 0)
        self.assertEqual(dx.shape, scores.shape)
        np.testing.assert_array_equal(dx[0, 2], np.zeros(4))
        np.testing.assert_array_equal(dx[1, 1], np.zeros(4))


if __name__ == "__main__":
    unittest.main()
