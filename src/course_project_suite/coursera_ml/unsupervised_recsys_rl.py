from __future__ import annotations
import numpy as np


def kmeans(X, k=3, iterations=30, seed=0):
    rng = np.random.default_rng(seed)
    centers = X[rng.choice(len(X), k, replace=False)].copy()
    for _ in range(iterations):
        labels = np.argmin(((X[:, None, :] - centers[None, :, :]) ** 2).sum(-1), axis=1)
        for i in range(k):
            if np.any(labels == i):
                centers[i] = X[labels == i].mean(0)
    labels = np.argmin(((X[:, None, :] - centers[None, :, :]) ** 2).sum(-1), axis=1)
    return centers, labels


def pca(X, n_components=2):
    Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ Vt[:n_components].T, Vt[:n_components], S[:n_components]


class GaussianAnomalyDetector:
    def __init__(self, percentile=5):
        self.percentile = percentile

    def fit(self, X):
        self.mu = X.mean(0)
        self.var = X.var(0) + 1e-6
        self.threshold = float(np.percentile(self.score(X), self.percentile))
        return self

    def score(self, X):
        return -0.5 * np.sum(np.log(2 * np.pi * self.var) + (X - self.mu) ** 2 / self.var, axis=1)

    def predict(self, X, threshold=None):
        cutoff = self.threshold if threshold is None else threshold
        return self.score(X) < cutoff


class MatrixFactorization:
    def __init__(self, n_factors=4, lr=0.03, reg=0.02, epochs=120, seed=0):
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.epochs = epochs
        self.seed = seed

    def fit(self, R, mask):
        rng = np.random.default_rng(self.seed)
        n, m = R.shape
        self.U = rng.normal(scale=0.1, size=(n, self.n_factors))
        self.V = rng.normal(scale=0.1, size=(m, self.n_factors))
        self.bu = np.zeros(n)
        self.bi = np.zeros(m)
        self.mean = R[mask].mean()
        rows, cols = np.where(mask)
        for _ in range(self.epochs):
            for i, j in zip(rows, cols):
                pred = self.mean + self.bu[i] + self.bi[j] + self.U[i] @ self.V[j]
                e = pred - R[i, j]
                ui = self.U[i].copy()
                vj = self.V[j].copy()
                self.bu[i] -= self.lr * (e + self.reg * self.bu[i])
                self.bi[j] -= self.lr * (e + self.reg * self.bi[j])
                self.U[i] -= self.lr * (e * vj + self.reg * ui)
                self.V[j] -= self.lr * (e * ui + self.reg * vj)
        return self

    def predict(self):
        return self.mean + self.bu[:, None] + self.bi[None, :] + self.U @ self.V.T


class EpsilonGreedyBandit:
    def __init__(self, k, epsilon=0.1):
        self.k = k
        self.epsilon = epsilon
        self.q = np.zeros(k)
        self.n = np.zeros(k)

    def act(self):
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.k)
        return int(np.argmax(self.q))

    def update(self, a, r):
        self.n[a] += 1
        self.q[a] += (r - self.q[a]) / self.n[a]
