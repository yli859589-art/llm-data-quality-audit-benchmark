from __future__ import annotations
import numpy as np
from course_project_suite.common import softmax, one_hot


def synthetic_data(w, b, num_examples, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(num_examples, len(w)))
    y = X @ np.asarray(w) + b + rng.normal(scale=0.01, size=num_examples)
    return X, y


def linreg(X, w, b):
    return X @ w + b


def squared_loss(y_hat, y):
    return ((y_hat - y) ** 2) / 2


def sgd(params, grads, lr, batch_size):
    for p, g in zip(params, grads):
        p -= lr * g / batch_size


def softmax_regression_train(X, y, num_classes, epochs=120, lr=0.2):
    W = np.zeros((X.shape[1], num_classes))
    b = np.zeros(num_classes)
    Y = one_hot(y, num_classes)
    for _ in range(epochs):
        P = softmax(X @ W + b, axis=1)
        d = (P - Y) / len(X)
        W -= lr * (X.T @ d)
        b -= lr * d.sum(0)
    return W, b


def corr2d(X, K):
    h, w = K.shape
    Y = np.zeros((X.shape[0] - h + 1, X.shape[1] - w + 1))
    for i in range(Y.shape[0]):
        for j in range(Y.shape[1]):
            Y[i, j] = (X[i : i + h, j : j + w] * K).sum()
    return Y


def masked_softmax(X, valid_lens):
    X = np.array(X, dtype=float)
    if valid_lens is not None:
        for i, l in enumerate(valid_lens):
            X[i, int(l) :] = -1e9
    return softmax(X, axis=-1)


def dot_product_attention(Q, K, V, valid_lens=None):
    scores = Q @ K.swapaxes(-1, -2) / np.sqrt(Q.shape[-1])
    if valid_lens is not None:
        for i, l in enumerate(valid_lens):
            scores[i, :, int(l) :] = -1e9
    weights = softmax(scores, axis=-1)
    return weights @ V, weights
