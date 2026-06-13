from __future__ import annotations

import json
import time

import torch

from localmax_v2_utils import ROOT, load_config, status_payload, write_report
from models_v2.config import ModelConfig
from models_v2.decoder_lm import DecoderLM, count_parameters


def main() -> None:
    training_cfg = load_config("configs/localmax_v2/training_matrix.yaml")
    model_matrix = load_config(training_cfg["model_config"])
    model_cfg = ModelConfig.from_mapping(model_matrix["models"][model_matrix["core_model"]])
    train = training_cfg["training"]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(13)
    model = DecoderLM(model_cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(train["learning_rate"]), weight_decay=float(train["weight_decay"]))
    context = int(train["context_length"])
    batch_size = int(train["micro_batch_size"])
    grad_accum = int(train["gradient_accumulation_steps"])
    benchmark_steps = 200
    started = time.perf_counter()
    for _ in range(benchmark_steps):
        optimizer.zero_grad(set_to_none=True)
        for _accum in range(grad_accum):
            x = torch.randint(0, model_cfg.vocab_size, (batch_size, context), dtype=torch.long, device=device)
            y = torch.randint(0, model_cfg.vocab_size, (batch_size, context), dtype=torch.long, device=device)
            if device == "cuda":
                with torch.amp.autocast("cuda", enabled=bool(train.get("mixed_precision", True))):
                    _, loss = model(x, y)
            else:
                _, loss = model(x, y)
            assert loss is not None
            (loss / grad_accum).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), float(train["gradient_clip"]))
        optimizer.step()
    elapsed = time.perf_counter() - started
    effective_batch_tokens = context * batch_size * grad_accum
    tokens_per_second = benchmark_steps * effective_batch_tokens / max(elapsed, 1e-9)
    min_tokens = int(train["min_tokens_seen_per_run"])
    steps_per_run = (min_tokens + effective_batch_tokens - 1) // effective_batch_tokens
    seconds_per_run = steps_per_run * effective_batch_tokens / max(tokens_per_second, 1e-9)
    estimated_24_run_hours = seconds_per_run * 24 / 3600.0
    ready = tokens_per_second > 0
    report = status_payload(
        "throughput",
        ready,
        [],
        {
            "status": "completed",
            "current_readiness": "LOCAL_MAX_V2_THROUGHPUT_BENCHMARKED",
            "device": device,
            "benchmark_steps": benchmark_steps,
            "context_length": context,
            "micro_batch_size": batch_size,
            "gradient_accumulation_steps": grad_accum,
            "effective_batch_tokens": effective_batch_tokens,
            "parameter_count": count_parameters(model),
            "tokens_per_second": tokens_per_second,
            "min_tokens_seen_per_run": min_tokens,
            "computed_steps_per_run_for_1m": steps_per_run,
            "estimated_seconds_per_run": seconds_per_run,
            "estimated_24_run_hours": estimated_24_run_hours,
            "selected_execution_tier": train["selected_tier"],
        },
    )
    write_report(report, "localmax_v2_throughput_report", "LocalMax V2 Training Throughput Report")
    print(json.dumps({"tokens_per_second": tokens_per_second, "estimated_24_run_hours": estimated_24_run_hours}))


if __name__ == "__main__":
    main()
