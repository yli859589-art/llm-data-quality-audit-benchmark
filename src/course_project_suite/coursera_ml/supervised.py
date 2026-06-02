from __future__ import annotations
import numpy as np
from course_project_suite.common import softmax, one_hot


class LinearRegressionGD:
    def __init__(self, lr=0.05, epochs=400, l2=0.0):
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2

    def fit(self, X, y):
        Xb = np.c_[np.ones(len(X)), X]
        self.theta = np.zeros(Xb.shape[1])
        for _ in range(self.epochs):
            pred = Xb @ self.theta
            grad = Xb.T @ (pred - y) / len(X) + self.l2 * np.r_[0, self.theta[1:]]
            self.theta -= self.lr * grad
        return self

    def predict(self, X):
        return np.c_[np.ones(len(X)), X] @ self.theta


class LogisticRegressionGD:
    def __init__(self, lr=0.1, epochs=300, l2=1e-3):
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2

    def fit(self, X, y):
        c = int(np.max(y) + 1)
        Xb = np.c_[np.ones(len(X)), X]
        self.W = np.zeros((Xb.shape[1], c))
        Y = one_hot(y, c)
        for _ in range(self.epochs):
            P = softmax(Xb @ self.W, axis=1)
            grad = Xb.T @ (P - Y) / len(X) + self.l2 * np.r_[np.zeros((1, c)), self.W[1:]]
            self.W -= self.lr * grad
        return self

    def predict_proba(self, X):
        return softmax(np.c_[np.ones(len(X)), X] @ self.W, axis=1)

    def predict(self, X):
        return np.argmax(self.predict_proba(X), axis=1)


def polynomial_features(x, degree=3):
    x = np.asarray(x).reshape(len(x), -1)
    return np.concatenate([x**p for p in range(1, degree + 1)], axis=1)
