from __future__ import annotations
import numpy as np
from collections import Counter
from course_project_suite.common import softmax, one_hot


class DenseNN:
    def __init__(self, dims, seed=0):
        rng = np.random.default_rng(seed)
        self.W = []
        self.b = []
        for a, b in zip(dims[:-1], dims[1:]):
            self.W.append(rng.normal(scale=np.sqrt(2 / a), size=(a, b)))
            self.b.append(np.zeros(b))

    def fit(self, X, y, lr=0.05, epochs=250):
        Y = one_hot(y, self.b[-1].size)
        for _ in range(epochs):
            A = [X]
            Z = []
            for W, b in zip(self.W[:-1], self.b[:-1]):
                z = A[-1] @ W + b
                Z.append(z)
                A.append(np.maximum(0, z))
            scores = A[-1] @ self.W[-1] + self.b[-1]
            P = softmax(scores, axis=1)
            delta = (P - Y) / len(X)
            dW = [None] * len(self.W)
            db = [None] * len(self.b)
            dW[-1] = A[-1].T @ delta
            db[-1] = delta.sum(0)
            dh = delta @ self.W[-1].T
            for i in reversed(range(len(self.W) - 1)):
                dz = dh * (Z[i] > 0)
                dW[i] = A[i].T @ dz
                db[i] = dz.sum(0)
                dh = dz @ self.W[i].T
            for i in range(len(self.W)):
                self.W[i] -= lr * dW[i]
                self.b[i] -= lr * db[i]
        return self

    def predict(self, X):
        A = X
        for W, b in zip(self.W[:-1], self.b[:-1]):
            A = np.maximum(0, A @ W + b)
        return np.argmax(A @ self.W[-1] + self.b[-1], axis=1)


class DecisionTree:
    def __init__(self, max_depth=4, min_leaf=2):
        self.max_depth = max_depth
        self.min_leaf = min_leaf

    def fit(self, X, y):
        self.tree = self._build(np.asarray(X), np.asarray(y), 0)
        return self

    def _entropy(self, y):
        cnt = np.array(list(Counter(y).values()), dtype=float)
        p = cnt / cnt.sum()
        return -np.sum(p * np.log2(p + 1e-12))

    def _build(self, X, y, depth):
        if depth >= self.max_depth or len(set(y)) == 1 or len(y) < 2 * self.min_leaf:
            return ("leaf", Counter(y).most_common(1)[0][0])
        base = self._entropy(y)
        best = (0, None, None)
        for j in range(X.shape[1]):
            for thr in np.unique(X[:, j]):
                m = X[:, j] <= thr
                if m.sum() < self.min_leaf or (~m).sum() < self.min_leaf:
                    continue
                gain = base - m.mean() * self._entropy(y[m]) - (~m).mean() * self._entropy(y[~m])
                if gain > best[0]:
                    best = (gain, j, thr)
        if best[1] is None:
            return ("leaf", Counter(y).most_common(1)[0][0])
        _, j, thr = best
        m = X[:, j] <= thr
        return (
            "node",
            j,
            thr,
            self._build(X[m], y[m], depth + 1),
            self._build(X[~m], y[~m], depth + 1),
        )

    def _pred(self, node, x):
        if node[0] == "leaf":
            return node[1]
        _, j, thr, l, r = node
        return self._pred(l, x) if x[j] <= thr else self._pred(r, x)

    def predict(self, X):
        return np.array([self._pred(self.tree, x) for x in X])
