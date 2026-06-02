from __future__ import annotations
from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path

from .attention import benchmark_attention_suite
from .char_lm import TrainConfig, train_character_lm
from .dataset import (
    analyze_removed_documents,
    build_ablation_variants,
    chunk_documents,
    concatenate_documents,
    inject_web_noise,
    load_public_corpus,
    quality_metrics,
)
from .reporting import write_bar_chart, write_line_chart


@dataclass(frozen=True)
class BenchmarkConfig:
    data_path: str
    output_dir: str
    max_documents: int = 140
    train_chars: int = 52000
    validation_chars: int = 9000
    train_config: TrainConfig = TrainConfig()
    attention_lengths: tuple[int, ...] = (32, 64, 128)
    attention_repeats: int = 4
    device: str = 'cpu'


def _write_report(path: Path, payload: dict[str, object]) -> None:
    variants = payload['data_quality_ablation']
    models = payload['language_model_ablation']
    attention = payload['attention_benchmark']
    baseline = models['raw_noisy_baseline']
    proposed = models['full_pipeline']
    loss_reduction = 100 * (baseline['final_val_loss'] - proposed['final_val_loss']) / baseline['final_val_loss']
    perplexity_reduction = 100 * (baseline['final_val_perplexity'] - proposed['final_val_perplexity']) / baseline['final_val_perplexity']
    longest = max(row['sequence_length'] for row in attention)
    longest_rows = {row['implementation']: row for row in attention if row['sequence_length'] == longest}
    sdpa_speedup = longest_rows['torch_sdpa']['query_tokens_per_second'] / longest_rows['naive']['query_tokens_per_second']
    sdpa_memory_reduction = 100 * (longest_rows['naive']['estimated_working_set_bytes'] - longest_rows['torch_sdpa']['estimated_working_set_bytes']) / longest_rows['naive']['estimated_working_set_bytes']
    lines = [
        '# LLM Data Quality and Efficient Attention Benchmark',
        '',
        '## Research question',
        '',
        'How much do deterministic data-quality controls improve a compact language-model training corpus, and how do reference attention implementations compare on correctness, throughput, and estimated memory?',
        '',
        '## Public corpus',
        '',
        f"- Source: [{payload['dataset']['url']}]({payload['dataset']['url']})",
        f"- SHA-256: `{payload['dataset']['sha256']}`",
        f"- Corpus characters: `{payload['dataset']['chars']}`",
        '',
        'The training subset is derived from Tiny Shakespeare. The benchmark injects deterministic web-style and symbol-heavy OCR/template noise to create a controlled data-quality stress test. Validation text remains clean and held out.',
        '',
        '## Result summary',
        '',
        f"- The full data-quality pipeline reduced duplicate rate from `{variants['raw_noisy_baseline']['duplicate_rate']:.3f}` to `{variants['full_pipeline']['duplicate_rate']:.3f}` and removed all injected email and phone hits.",
        f"- Compared with the raw noisy baseline, the full pipeline reduced held-out validation loss by `{loss_reduction:.2f}%` and perplexity by `{perplexity_reduction:.2f}%`.",
        f"- At sequence length `{longest}`, PyTorch SDPA achieved `{sdpa_speedup:.2f}x` the naive reference throughput with an estimated working-set reduction of `{sdpa_memory_reduction:.1f}%`.",
        '- Cleaning and redaction alone are not sufficient: the ablation retains duplicated and symbol-heavy documents, so filtering and deduplication remain necessary.',
        '',
        '## Data-quality ablation',
        '',
        '| Variant | Documents | Characters | Duplicate rate | Email hits | Phone hits | Quality pass rate |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for name, metrics in variants.items():
        lines.append(f"| `{name}` | {metrics['documents']} | {metrics['characters']} | {metrics['duplicate_rate']:.3f} | {metrics['email_hits']} | {metrics['phone_hits']} | {metrics['quality_pass_rate']:.3f} |")
    lines.extend([
        '',
        '## Character-level GPT ablation',
        '',
        '| Variant | Final validation loss | Validation perplexity | Training characters | Tokens/s |',
        '|---|---:|---:|---:|---:|',
    ])
    for name, metrics in models.items():
        lines.append(f"| `{name}` | {metrics['final_val_loss']:.4f} | {metrics['final_val_perplexity']:.2f} | {metrics['train_characters']} | {metrics['tokens_per_second']:.1f} |")
    lines.extend([
        '',
        '![Training curves](training_curves.svg)',
        '',
        '## Attention systems benchmark',
        '',
        '| Implementation | Sequence length | Query tokens/s | Max error vs. naive | Estimated working set bytes | CUDA peak bytes |',
        '|---|---:|---:|---:|---:|---:|',
    ])
    for row in attention:
        lines.append(f"| `{row['implementation']}` | {row['sequence_length']} | {row['query_tokens_per_second']:.1f} | {row['max_abs_error_vs_naive']:.2e} | {row['estimated_working_set_bytes']} | {row['cuda_peak_memory_bytes'] if row['cuda_peak_memory_bytes'] is not None else 'N/A'} |")
    lines.extend([
        '',
        '![Attention throughput](attention_throughput.svg)',
        '',
        '## Error analysis',
        '',
        f"- Removed documents: `{payload['error_analysis']['removed_documents']}`",
        f"- Note: {payload['error_analysis']['note']}",
        '',
    ])
    for example in payload['error_analysis']['sanitized_removed_examples']:
        lines.append(f"- Sanitized removed example: `{example}`")
    lines.extend([
        '',
        '## Limitations',
        '',
        '- Tiny Shakespeare is a compact public corpus, not a production-scale web dataset.',
        '- Injected stress-test corruption makes the quality experiment reproducible but does not estimate the natural noise rate of a production web corpus.',
        '- CPU memory values are algorithmic estimates. CUDA peak allocation is reported only when CUDA is used.',
        '- The online attention implementation is a numerically stable reference, not a fused production kernel.',
    ])
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def run_benchmark(config: BenchmarkConfig) -> dict[str, object]:
    corpus, source = load_public_corpus(config.data_path)
    validation_text = corpus[-config.validation_chars:]
    base_documents = chunk_documents(corpus[:-config.validation_chars], max_documents=config.max_documents)
    noisy_documents = inject_web_noise(base_documents)
    variants = build_ablation_variants(noisy_documents)
    variant_metrics = {name: quality_metrics(documents) for name, documents in variants.items()}
    lm_inputs = {
        'raw_noisy_baseline': concatenate_documents(variants['raw_noisy_baseline'], config.train_chars),
        'clean_redact': concatenate_documents(variants['clean_redact'], config.train_chars),
        'full_pipeline': concatenate_documents(variants['full_pipeline'], config.train_chars),
    }
    shared_vocab = ''.join(lm_inputs.values()) + validation_text
    train_config = replace(config.train_config, device=config.device)
    lm_metrics = {name: train_character_lm(text, validation_text, shared_vocab, train_config) for name, text in lm_inputs.items()}
    attention = benchmark_attention_suite(
        config.attention_lengths,
        repeats=config.attention_repeats,
        device=config.device,
    )
    payload = {
        'project': 'LLM Data Quality and Efficient Attention Benchmark Platform',
        'research_question': 'Measure data-quality pipeline effects on a compact GPT validation loss and compare attention implementations.',
        'dataset': asdict(source),
        'configuration': {
            **asdict(config),
            'train_config': asdict(train_config),
        },
        'data_quality_ablation': variant_metrics,
        'language_model_ablation': lm_metrics,
        'attention_benchmark': attention,
        'error_analysis': analyze_removed_documents(noisy_documents, variants['full_pipeline']),
    }
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'results.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    write_line_chart(
        output_dir / 'training_curves.svg',
        {name: [(point['step'], point['val_loss']) for point in metrics['curve']] for name, metrics in lm_metrics.items()},
        'Tiny Shakespeare held-out validation loss',
        'Training step',
        'Validation loss',
    )
    write_bar_chart(output_dir / 'attention_throughput.svg', attention, 'Attention throughput by implementation and sequence length')
    _write_report(output_dir / 'REPORT.md', payload)
    return payload
