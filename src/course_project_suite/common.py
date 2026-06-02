from __future__ import annotations
import math, random, json, time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, Callable, Any
import numpy as np

try:
    import torch
except Exception:  # pragma: no cover
    torch = None


def set_seed(seed: int = 7) -> None:
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    z = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(z)
    return e / np.sum(e, axis=axis, keepdims=True)


def accuracy(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    return float(np.mean(np.asarray(y_pred) == np.asarray(y_true)))


def one_hot(y: np.ndarray, num_classes: int) -> np.ndarray:
    out = np.zeros((len(y), num_classes), dtype=float)
    out[np.arange(len(y)), y.astype(int)] = 1.0
    return out


def train_val_split(X, y, val_fraction: float = 0.2, seed: int = 0):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))
    n_val = int(len(X) * val_fraction)
    val_idx, train_idx = idx[:n_val], idx[n_val:]
    return X[train_idx], X[val_idx], y[train_idx], y[val_idx]


def make_classification(n=120, d=4, c=3, seed=0):
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(c, d)) * 2.0
    y = rng.integers(0, c, size=n)
    X = centers[y] + rng.normal(scale=0.55, size=(n, d))
    return X.astype(np.float64), y.astype(np.int64)


def make_regression(n=100, d=3, seed=1):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    w = rng.normal(size=d)
    y = X @ w + 0.25 * rng.normal(size=n)
    return X.astype(np.float64), y.astype(np.float64), w.astype(np.float64)


def numerical_gradient(
    f: Callable[[np.ndarray], float], x: np.ndarray, h: float = 1e-5
) -> np.ndarray:
    grad = np.zeros_like(x, dtype=np.float64)
    it = np.nditer(x, flags=["multi_index"], op_flags=["readwrite"])
    while not it.finished:
        idx = it.multi_index
        old = x[idx]
        x[idx] = old + h
        fxph = f(x)
        x[idx] = old - h
        fxmh = f(x)
        x[idx] = old
        grad[idx] = (fxph - fxmh) / (2 * h)
        it.iternext()
    return grad


def rel_error(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.max(np.abs(x - y) / np.maximum(1e-8, np.abs(x) + np.abs(y))))


@dataclass
class CheckResult:
    name: str
    ok: bool
    metrics: dict[str, Any]

    def to_dict(self):
        def clean(v):
            if isinstance(v, dict):
                return {str(k): clean(val) for k, val in v.items()}
            if isinstance(v, (list, tuple)):
                return [clean(x) for x in v]
            if isinstance(v, (np.integer,)):
                return int(v)
            if isinstance(v, (np.floating,)):
                return float(v)
            if isinstance(v, (np.bool_,)):
                return bool(v)
            return v

        return {"name": self.name, "ok": bool(self.ok), "metrics": clean(self.metrics)}


def save_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
