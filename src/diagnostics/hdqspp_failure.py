from __future__ import annotations

from statistics import mean

from analysis.quality_error_analysis import (
    document_metrics,
    js_divergence,
    kl_divergence,
    length_distribution,
    pearson_correlation,
    safe_excerpt,
    token_distribution,
)
from course_project_suite.llm_benchmark.quality import score_documents
from filters.hdqspp_v2 import HDQSv2Config, select_hdqspp_v2


def summarize_hdqspp_failure(
    train_documents: list[str],
    dev_documents: list[str],
    test_documents: list[str],
    *,
    retention_ratio: float,
    v2_config: HDQSv2Config,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    dev_tokens = token_distribution(dev_documents, top_k=5000)
    v1_scores = score_documents(train_documents)
    v1_ranked = sorted(v1_scores, key=lambda row: row.score, reverse=True)
    v1_keep = max(1, round(len(train_documents) * retention_ratio))
    v1_kept = {row.index for row in v1_ranked[:v1_keep]}
    v2_docs, v2_scores = select_hdqspp_v2(
        train_documents,
        reference_documents=dev_documents,
        config=v2_config,
    )
    v2_kept = {row.index for row in v2_scores if train_documents[row.index] in set(v2_docs)}
    v2_by_index = {row.index: row for row in v2_scores}

    rows: list[dict[str, object]] = []
    for score_row in v1_scores:
        document = train_documents[score_row.index]
        metrics = document_metrics(document, dev_tokens)
        v2_row = v2_by_index[score_row.index]
        rows.append(
            {
                "split": "train",
                "document_index": score_row.index,
                "hdqspp_score": score_row.score,
                "hdqspp_v2_score": v2_row.score,
                "kept_by_hdqspp": score_row.index in v1_kept,
                "kept_by_hdqspp_v2": score_row.index in v2_kept,
                "excerpt": safe_excerpt(document),
                **metrics,
                **{f"component_{key}": value for key, value in score_row.components.items()},
                **{f"v2_component_{key}": value for key, value in v2_row.components.items()},
            }
        )

    v1_docs = [doc for index, doc in enumerate(train_documents) if index in v1_kept]
    raw_tokens = token_distribution(train_documents, top_k=5000)
    v1_tokens = token_distribution(v1_docs, top_k=5000)
    v2_tokens = token_distribution(v2_docs, top_k=5000)
    raw_lengths = length_distribution(train_documents)
    v1_lengths = length_distribution(v1_docs)
    v2_lengths = length_distribution(v2_docs)
    dev_lengths = length_distribution(dev_documents)
    test_lengths = length_distribution(test_documents)

    component_correlations = {}
    proxy = [float(row["dev_loss_proxy"]) for row in rows]
    for key in [
        "hdqspp_score",
        "hdqspp_v2_score",
        "token_diversity",
        "repetition_rate",
        "token_entropy",
        "char_entropy",
        "symbol_fraction",
        "information_density",
    ]:
        component_correlations[key] = pearson_correlation(
            [float(row[key]) for row in rows],
            proxy,
        )

    kept_rows = [row for row in rows if row["kept_by_hdqspp"]]
    dropped_rows = [row for row in rows if not row["kept_by_hdqspp"]]
    summary = {
        "dataset_key": "wikitext2_paper",
        "dataset_scope": "official_split",
        "source": "real WikiText-2 local official split artifacts",
        "target_keep_rate": retention_ratio,
        "raw_keep_rate": 1.0,
        "random_same_keep_rate": retention_ratio,
        "hdqspp_keep_rate": len(v1_docs) / max(1, len(train_documents)),
        "hdqspp_v2_keep_rate": len(v2_docs) / max(1, len(train_documents)),
        "hdqspp_kept_mean_token_count": mean(float(row["token_count"]) for row in kept_rows),
        "hdqspp_dropped_mean_token_count": mean(float(row["token_count"]) for row in dropped_rows),
        "hdqspp_kept_mean_diversity": mean(float(row["token_diversity"]) for row in kept_rows),
        "hdqspp_dropped_mean_diversity": mean(
            float(row["token_diversity"]) for row in dropped_rows
        ),
        "hdqspp_kept_mean_repetition": mean(float(row["repetition_rate"]) for row in kept_rows),
        "hdqspp_dropped_mean_repetition": mean(
            float(row["repetition_rate"]) for row in dropped_rows
        ),
        "hdqspp_kept_mean_entropy": mean(float(row["token_entropy"]) for row in kept_rows),
        "hdqspp_dropped_mean_entropy": mean(float(row["token_entropy"]) for row in dropped_rows),
        "token_kl_hdqspp_vs_raw": kl_divergence(v1_tokens, raw_tokens),
        "token_js_hdqspp_vs_raw": js_divergence(v1_tokens, raw_tokens),
        "token_js_hdqspp_v2_vs_raw": js_divergence(v2_tokens, raw_tokens),
        "length_js_hdqspp_vs_raw": js_divergence(v1_lengths, raw_lengths),
        "length_js_hdqspp_v2_vs_raw": js_divergence(v2_lengths, raw_lengths),
        "length_js_raw_train_vs_dev": js_divergence(raw_lengths, dev_lengths),
        "length_js_hdqspp_train_vs_dev": js_divergence(v1_lengths, dev_lengths),
        "length_js_hdqspp_v2_train_vs_dev": js_divergence(v2_lengths, dev_lengths),
        "length_js_raw_train_vs_test_posthoc": js_divergence(raw_lengths, test_lengths),
        "length_js_hdqspp_train_vs_test_posthoc": js_divergence(v1_lengths, test_lengths),
        "length_js_hdqspp_v2_train_vs_test_posthoc": js_divergence(v2_lengths, test_lengths),
        "component_correlations_with_dev_loss_proxy": component_correlations,
        "top_dropped_examples": sorted(
            dropped_rows,
            key=lambda row: float(row["dev_loss_proxy"]),
        )[:10],
        "top_kept_low_quality_examples": sorted(
            kept_rows,
            key=lambda row: float(row["hdqspp_score"]),
        )[:10],
        "failure_hypotheses": [
            "HDQS++ v1 uses hard filtering at the target keep rate, reducing narrative context.",
            "The v1 score can over-penalize formatting symbols and normal repetition.",
            "The v1 kept set shifts token and length distributions away from raw train data.",
        ],
    }
    return rows, summary
