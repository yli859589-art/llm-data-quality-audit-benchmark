from __future__ import annotations

import platform
import statistics
import time

import torch

from course_project_suite.cs336.systems import (
    naive_attention,
    online_attention,
    torch_sdpa_attention,
)


def _synchronize(device: str) -> None:
    if device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.synchronize()


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _measure(
    function, q, k, v, repeats: int, device: str
) -> tuple[torch.Tensor, dict[str, float], int | None]:
    for _ in range(2):
        output = function(q, k, v)
    _synchronize(device)
    if device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        output = function(q, k, v)
        _synchronize(device)
        samples.append(time.perf_counter() - started)
    peak = (
        torch.cuda.max_memory_allocated()
        if device.startswith("cuda") and torch.cuda.is_available()
        else None
    )
    timings = {
        "median_seconds_per_call": statistics.median(samples),
        "p25_seconds_per_call": _percentile(samples, 0.25),
        "p75_seconds_per_call": _percentile(samples, 0.75),
    }
    return output, timings, peak


def _estimated_bytes(name: str, batch: int, heads: int, seq: int, dim: int, bytes_per: int) -> int:
    qkv = 3 * batch * heads * seq * dim * bytes_per
    output = batch * heads * seq * dim * bytes_per
    scores = batch * heads * seq * seq * bytes_per
    return qkv + output + (0 if name == "torch_sdpa" else scores)


def attention_environment(device: str) -> dict[str, object]:
    return {
        "hardware": platform.processor() or platform.machine(),
        "platform": platform.platform(),
        "pytorch_version": torch.__version__,
        "device": device,
        "dtype": "float32",
        "torch_num_threads": torch.get_num_threads(),
        "cuda_available": torch.cuda.is_available(),
    }


def benchmark_attention_suite(
    seq_lengths: tuple[int, ...] = (32, 64, 128),
    *,
    batch: int = 1,
    heads: int = 2,
    dim: int = 32,
    repeats: int = 4,
    device: str = "cpu",
    seed: int = 31,
) -> list[dict[str, object]]:
    torch.manual_seed(seed)
    implementations = {
        "naive": naive_attention,
        "online_reference": online_attention,
        "torch_sdpa": torch_sdpa_attention,
    }
    rows = []
    for seq in seq_lengths:
        q = torch.randn(batch, heads, seq, dim, device=device)
        k = torch.randn_like(q)
        v = torch.randn_like(q)
        baseline, _, _ = _measure(naive_attention, q, k, v, 1, device)
        for name, function in implementations.items():
            output, timings, peak = _measure(function, q, k, v, repeats, device)
            median = timings["median_seconds_per_call"]
            rows.append(
                {
                    "implementation": name,
                    "sequence_length": seq,
                    **timings,
                    "seconds_per_call": median,
                    "query_tokens_per_second": batch * seq / max(median, 1e-12),
                    "max_abs_error_vs_naive": float((output - baseline).abs().max()),
                    "estimated_working_set_bytes": _estimated_bytes(
                        name, batch, heads, seq, dim, q.element_size()
                    ),
                    "cuda_peak_memory_bytes": peak,
                    "memory_note": (
                        "Algorithmic working-set bytes are estimates. "
                        "CUDA peak allocation is reported only when CUDA is used."
                    ),
                }
            )
    return rows
