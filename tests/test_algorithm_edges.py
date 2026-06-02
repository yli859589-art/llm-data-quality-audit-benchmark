import random
import unittest

import numpy as np

from course_project_suite.common import numerical_gradient, rel_error
from course_project_suite.cs188.inference import ParticleFilter
from course_project_suite.cs188.multiagent import ExpectimaxAgent, MinimaxAgent
from course_project_suite.cs188.pacman_core import TINY_LAYOUT, parse_layout
from course_project_suite.cs188.rl import QLearningAgent
from course_project_suite.cs231n.layers import (
    batchnorm_backward,
    batchnorm_forward,
    max_pool_backward_naive,
    max_pool_forward_naive,
)
from course_project_suite.cs231n.sequence import rnn_step_backward, rnn_step_forward
from course_project_suite.cs336.data import clean_common_crawl_text, exact_deduplicate, quality_filter, redact_pii


class AlgorithmEdgeTests(unittest.TestCase):
    def test_multiagent_search_returns_legal_actions(self):
        game = parse_layout(TINY_LAYOUT)
        legal = game.legal_actions(0)
        self.assertIn(MinimaxAgent(depth=1).get_action(game), legal)
        self.assertIn(ExpectimaxAgent(depth=1).get_action(game), legal)

    def test_q_learning_update_uses_bootstrap_value(self):
        agent = QLearningAgent(['left', 'right'], alpha=.5, epsilon=0.0, gamma=.9)
        agent.Q[('next', 'right')] = 2.0
        agent.update('start', 'left', 'next', 1.0)
        self.assertAlmostEqual(agent.get_q_value('start', 'left'), 1.4)

    def test_particle_filter_concentrates_on_likely_state(self):
        random.seed(4)
        likelihood = lambda observation, state: .95 if state == observation else .05
        filt = ParticleFilter([0, 1], lambda state: state, likelihood, num_particles=600)
        filt.observe(1)
        self.assertGreater(filt.belief().get(1, 0.0), .85)

    def test_batchnorm_gradient(self):
        np.random.seed(5)
        x = np.random.randn(5, 4); gamma = np.random.randn(4); beta = np.random.randn(4); dout = np.random.randn(5, 4)
        _, cache = batchnorm_forward(x, gamma, beta); dx, dgamma, dbeta = batchnorm_backward(dout, cache)
        fx = lambda xx: np.sum(batchnorm_forward(xx, gamma, beta)[0] * dout)
        fg = lambda gg: np.sum(batchnorm_forward(x, gg, beta)[0] * dout)
        fb = lambda bb: np.sum(batchnorm_forward(x, gamma, bb)[0] * dout)
        self.assertLess(rel_error(dx, numerical_gradient(fx, x.copy())), 1e-6)
        self.assertLess(rel_error(dgamma, numerical_gradient(fg, gamma.copy())), 1e-7)
        self.assertLess(rel_error(dbeta, numerical_gradient(fb, beta.copy())), 1e-7)

    def test_max_pool_gradient(self):
        x = np.array([[[[1.0, 3.0], [2.0, 4.0]]]])
        out, cache = max_pool_forward_naive(x, {'pool_height': 2, 'pool_width': 2, 'stride': 2})
        dx = max_pool_backward_naive(np.ones_like(out), cache)
        np.testing.assert_array_equal(dx, np.array([[[[0.0, 0.0], [0.0, 1.0]]]]))

    def test_rnn_step_gradient(self):
        np.random.seed(6)
        x = np.random.randn(2, 3); prev = np.random.randn(2, 4); wx = np.random.randn(3, 4); wh = np.random.randn(4, 4); b = np.random.randn(4); dout = np.random.randn(2, 4)
        _, cache = rnn_step_forward(x, prev, wx, wh, b); dx, dprev, dwx, dwh, db = rnn_step_backward(dout, cache)
        fx = lambda xx: np.sum(rnn_step_forward(xx, prev, wx, wh, b)[0] * dout)
        fp = lambda pp: np.sum(rnn_step_forward(x, pp, wx, wh, b)[0] * dout)
        self.assertLess(rel_error(dx, numerical_gradient(fx, x.copy())), 1e-7)
        self.assertLess(rel_error(dprev, numerical_gradient(fp, prev.copy())), 1e-7)
        self.assertEqual(dwx.shape, wx.shape); self.assertEqual(dwh.shape, wh.shape); self.assertEqual(db.shape, b.shape)

    def test_data_cleaning_redaction_and_deduplication(self):
        raw = '<p>Email test@example.org or call +1 412 555 0199.</p> https://example.org'
        clean = redact_pii(clean_common_crawl_text(raw))
        self.assertNotIn('test@example.org', clean)
        self.assertNotIn('412 555', clean)
        self.assertIn('<EMAIL>', clean)
        self.assertEqual(exact_deduplicate([clean, clean]), [clean])
        self.assertFalse(quality_filter('$$$ !!!'))


if __name__ == '__main__':
    unittest.main()
