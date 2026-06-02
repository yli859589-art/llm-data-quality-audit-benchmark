import unittest
import numpy as np
import torch
from course_project_suite.run_all import run_all
from course_project_suite.common import numerical_gradient, rel_error
from course_project_suite.cs231n.layers import (
    affine_forward,
    affine_backward,
    conv_forward_naive,
    conv_backward_naive,
    batchnorm_forward,
    batchnorm_backward,
)
from course_project_suite.coursera_ml.unsupervised_recsys_rl import kmeans, GaussianAnomalyDetector
from course_project_suite.cs188.inference import forward_filter
from course_project_suite.cs336.optim import AdamW, cosine_lr
from course_project_suite.cs336.tokenizer import BPETokenizer
from course_project_suite.cs336.systems import naive_attention, torch_sdpa_attention


class SmokeTests(unittest.TestCase):
    def test_all_runners(self):
        results = run_all()
        self.assertTrue(all(r.ok for r in results), [r.to_dict() for r in results])

    def test_affine_gradient(self):
        np.random.seed(0)
        x = np.random.randn(4, 3)
        w = np.random.randn(3, 5)
        b = np.random.randn(5)
        dout = np.random.randn(4, 5)
        out, cache = affine_forward(x, w, b)
        dx, dw, db = affine_backward(dout, cache)
        f = lambda xx: np.sum(affine_forward(xx, w, b)[0] * dout)
        self.assertLess(rel_error(dx, numerical_gradient(f, x.copy())), 1e-7)

    def test_conv_gradient(self):
        np.random.seed(1)
        x = np.random.randn(1, 1, 4, 4)
        w = np.random.randn(1, 1, 3, 3)
        b = np.random.randn(1)
        dout = np.random.randn(1, 1, 4, 4)
        out, cache = conv_forward_naive(x, w, b, {"stride": 1, "pad": 1})
        dx, dw, db = conv_backward_naive(dout, cache)
        fx = lambda xx: np.sum(conv_forward_naive(xx, w, b, {"stride": 1, "pad": 1})[0] * dout)
        fw = lambda ww: np.sum(conv_forward_naive(x, ww, b, {"stride": 1, "pad": 1})[0] * dout)
        fb = lambda bb: np.sum(conv_forward_naive(x, w, bb, {"stride": 1, "pad": 1})[0] * dout)
        self.assertLess(rel_error(dx, numerical_gradient(fx, x.copy())), 1e-7)
        self.assertLess(rel_error(dw, numerical_gradient(fw, w.copy())), 1e-7)
        self.assertLess(rel_error(db, numerical_gradient(fb, b.copy())), 1e-7)

    def test_bpe_roundtrip(self):
        tok = BPETokenizer().train(["hello world hello"], num_merges=10)
        ids = tok.encode("hello")
        self.assertTrue(len(ids) > 0)
        self.assertIn("hello", tok.decode(ids))

    def test_attention_matches_sdpa(self):
        torch.manual_seed(0)
        q = torch.randn(1, 2, 8, 4)
        k = torch.randn_like(q)
        v = torch.randn_like(q)
        a = naive_attention(q, k, v)
        b = torch_sdpa_attention(q, k, v)
        self.assertLess(float((a - b).abs().max()), 1e-5)

    def test_kmeans_labels_match_final_centers(self):
        rng = np.random.default_rng(123)
        X = rng.normal(size=(8, 2))
        centers, labels = kmeans(X, k=3, iterations=1, seed=5)
        expected = np.argmin(((X[:, None, :] - centers[None, :, :]) ** 2).sum(-1), axis=1)
        np.testing.assert_array_equal(labels, expected)

    def test_anomaly_detector_uses_training_threshold(self):
        X = np.array([[0.0], [0.1], [-0.1], [0.05], [-0.05]])
        detector = GaussianAnomalyDetector().fit(X)
        self.assertTrue(bool(detector.predict(np.array([[100.0]]))[0]))

    def test_adamw_closure_allows_gradients(self):
        p = torch.tensor([1.0], requires_grad=True)
        opt = AdamW([p], lr=1e-3)

        def closure():
            opt.zero_grad()
            loss = (p**2).sum()
            loss.backward()
            return loss

        loss = opt.step(closure)
        self.assertGreater(float(loss.detach()), 0.0)
        self.assertLess(float(p.detach()), 1.0)

    def test_cosine_lr_clamps_after_schedule(self):
        self.assertEqual(cosine_lr(100, 100, 5, 1e-3), 0.0)
        self.assertEqual(cosine_lr(200, 100, 5, 1e-3), 0.0)

    def test_forward_filter_normalizes_each_step(self):
        states = ["H", "C"]
        obs = ["walk", "shop", "clean"]
        start = {"H": 0.6, "C": 0.4}
        trans = {"H": {"H": 0.7, "C": 0.3}, "C": {"H": 0.4, "C": 0.6}}
        emit = {
            "H": {"walk": 0.6, "shop": 0.3, "clean": 0.1},
            "C": {"walk": 0.1, "shop": 0.4, "clean": 0.5},
        }
        history = forward_filter(obs, states, start, trans, emit)
        self.assertEqual(len(history), len(obs))
        for belief in history:
            self.assertAlmostEqual(sum(belief.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
