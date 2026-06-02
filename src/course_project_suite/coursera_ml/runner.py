from __future__ import annotations
import numpy as np
from course_project_suite.common import (
    CheckResult,
    make_classification,
    make_regression,
    accuracy,
    set_seed,
    train_val_split,
)
from .supervised import LinearRegressionGD, LogisticRegressionGD
from .advanced import DenseNN, DecisionTree
from .unsupervised_recsys_rl import kmeans, GaussianAnomalyDetector, MatrixFactorization


def run():
    set_seed(2)
    Xr, yr, w = make_regression(n=180, d=3, seed=2)
    Xr_train, Xr_val, yr_train, yr_val = train_val_split(Xr, yr, val_fraction=0.25, seed=2)
    lin = LinearRegressionGD().fit(Xr_train, yr_train)
    rmse = float(np.sqrt(np.mean((lin.predict(Xr_val) - yr_val) ** 2)))
    X, y = make_classification(n=240, d=5, c=3, seed=4)
    X_train, X_val, y_train, y_val = train_val_split(X, y, val_fraction=0.25, seed=4)
    log = LogisticRegressionGD(epochs=350).fit(X_train, y_train)
    log_acc = accuracy(log.predict(X_val), y_val)
    nn = DenseNN([5, 12, 3], seed=3).fit(X_train, y_train, epochs=250)
    nn_acc = accuracy(nn.predict(X_val), y_val)
    tree = DecisionTree(max_depth=4).fit(X_train, y_train)
    tree_acc = accuracy(tree.predict(X_val), y_val)
    centers, labels = kmeans(X_train, k=3, seed=5)
    anomaly_probe = np.vstack([X_val, np.full((1, X.shape[1]), 25.0)])
    anomalies = GaussianAnomalyDetector().fit(X_train).predict(anomaly_probe)
    rng = np.random.default_rng(9)
    true_u = rng.normal(size=(14, 3))
    true_v = rng.normal(size=(12, 3))
    R = 3.0 + true_u @ true_v.T
    observed = rng.random(R.shape) < 0.8
    pairs = np.argwhere(observed)
    rng.shuffle(pairs)
    n_val = max(1, len(pairs) // 5)
    train_mask = np.zeros_like(observed)
    val_mask = np.zeros_like(observed)
    for i, j in pairs[n_val:]:
        train_mask[i, j] = True
    for i, j in pairs[:n_val]:
        val_mask[i, j] = True
    mf = MatrixFactorization(n_factors=3, lr=0.02, reg=0.01, epochs=300, seed=9).fit(R, train_mask)
    pred = mf.predict()
    mf_train_mse = float(np.mean((pred[train_mask] - R[train_mask]) ** 2))
    mf_val_mse = float(np.mean((pred[val_mask] - R[val_mask]) ** 2))
    metrics = {
        "lin_val_rmse": rmse,
        "log_val_acc": log_acc,
        "nn_val_acc": nn_acc,
        "tree_val_acc": tree_acc,
        "kmeans_clusters": int(len(set(labels))),
        "anomaly_probe_detected": bool(anomalies[-1]),
        "mf_train_mse": mf_train_mse,
        "mf_val_mse": mf_val_mse,
    }
    ok = (
        rmse < 0.45
        and log_acc > 0.9
        and nn_acc > 0.9
        and tree_acc > 0.8
        and anomalies[-1]
        and mf_val_mse < 1.5
    )
    return CheckResult("coursera_ml_specialization_public_alignment", ok, metrics)
