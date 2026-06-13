from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

from .base import BaseFilter, FilterDecision, FilterInput
from .cost import build_cost_report
from .diversity import build_diversity_report
from .io import project_relative, write_json, write_jsonl
from .keep_rate import keep_count_for_rate, validate_keep_rate
from .manifest import create_filter_manifest, sha256_file
from .risk import build_risk_report
from .urd_components import (
    disabled_components_from_config,
    pareto_layers,
    score_cost,
    score_diversity,
    score_risk,
    score_shift,
    score_utility,
)


DEFAULT_WEIGHTS = {
    "alpha": 0.35,
    "beta": 0.25,
    "gamma": 0.20,
    "lambda_shift": 0.10,
    "mu_cost": 0.10,
}


def _weights(params: dict[str, Any]) -> dict[str, float]:
    return {name: float(params.get(name, DEFAULT_WEIGHTS[name])) for name in DEFAULT_WEIGHTS}


def _selection_mode(filter_name: str, params: dict[str, Any]) -> str:
    configured = str(params.get("selection_mode", "")).strip()
    if configured:
        return configured
    return "pareto" if filter_name == "urd_pareto" else "fixed_weight"


def _zero_component(row: dict[str, Any], component: str) -> None:
    if component == "utility":
        row["utility_score"] = 0.0
        row["utility_components"] = {"disabled_by_ablation": True}
        row["utility_notes"] = "Disabled by Step 6 URD ablation config."
    elif component == "risk":
        row["risk_score"] = 0.0
        row["risk_components"] = {"disabled_by_ablation": True}
        row["risk_notes"] = "Disabled by Step 6 URD ablation config."
    elif component == "diversity":
        row["diversity_score"] = 0.0
        row["diversity_components"] = {"disabled_by_ablation": True}
        row["diversity_notes"] = "Disabled by Step 6 URD ablation config."
    elif component == "shift":
        row["shift_penalty"] = 0.0
        row["shift_components"] = {"disabled_by_ablation": True}
        row["shift_notes"] = "Disabled by Step 6 URD ablation config."
    elif component == "cost":
        row["cost_score"] = 0.0
        row["cost_components"] = {"disabled_by_ablation": True}
        row["cost_notes"] = "Disabled by Step 6 URD ablation config."


class URDSelectorFilter(BaseFilter):
    filter_type = "urd_selector"
    proxy_used = True

    def __init__(self, config) -> None:
        super().__init__(config)
        self.selection_mode = _selection_mode(config.filter_name, config.params)
        self.weights = _weights(config.params)
        self.disabled_components = disabled_components_from_config(config.params, config.filter_name)
        self._component_rows: list[dict[str, Any]] = []
        self._pareto_payload: dict[str, Any] = {}

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("URDSelectorFilter uses batch-level selection")

    def _component_row(self, record: FilterInput, records: list[FilterInput]) -> dict[str, Any]:
        row: dict[str, Any] = {"doc_id": record.doc_id, "source": record.source, "estimated_tokens": record.estimated_tokens}
        row.update(score_utility(record, records))
        row.update(score_risk(record, records))
        row.update(score_diversity(record, records))
        row.update(score_shift(record, records))
        row.update(score_cost(record, records))
        for component in sorted(self.disabled_components):
            _zero_component(row, component)
        row["proxy_components"] = ["utility", "risk", "diversity", "shift", "cost"]
        row["disabled_components"] = sorted(self.disabled_components)
        return row

    def _fixed_weight_score(self, row: dict[str, Any]) -> float:
        return (
            self.weights["alpha"] * float(row["utility_score"])
            + self.weights["beta"] * float(row["diversity_score"])
            - self.weights["gamma"] * float(row["risk_score"])
            - self.weights["lambda_shift"] * float(row["shift_penalty"])
            - self.weights["mu_cost"] * float(row["cost_score"])
        )

    def _select_fixed(self, rows: list[dict[str, Any]]) -> set[str]:
        for row in rows:
            row["urd_score"] = self._fixed_weight_score(row)
            row["selection_mode"] = "fixed_weight"
        keep_count = keep_count_for_rate(len(rows), self.config.target_keep_rate)
        ranked = sorted(rows, key=lambda item: (-float(item["urd_score"]), str(item["doc_id"])))
        return {str(row["doc_id"]) for row in ranked[:keep_count]}

    def _select_pareto(self, rows: list[dict[str, Any]]) -> set[str]:
        payload = pareto_layers(rows)
        ranks = payload["ranks"]
        for row in rows:
            row["pareto_rank"] = int(ranks[str(row["doc_id"])])
            row["tie_break_score"] = self._fixed_weight_score(row)
            row["urd_score"] = row["tie_break_score"]
            row["selection_mode"] = "pareto"
        keep_count = keep_count_for_rate(len(rows), self.config.target_keep_rate)
        ranked = sorted(rows, key=lambda item: (int(item["pareto_rank"]), -float(item["tie_break_score"]), str(item["doc_id"])))
        self._pareto_payload = payload
        return {str(row["doc_id"]) for row in ranked[:keep_count]}

    def filter(self, records: list[FilterInput]):
        started = time.perf_counter()
        rows = [self._component_row(record, records) for record in records]
        if self.selection_mode == "pareto":
            kept_ids = self._select_pareto(rows)
        else:
            kept_ids = self._select_fixed(rows)
        decisions = []
        for row in rows:
            keep = str(row["doc_id"]) in kept_ids
            decisions.append(
                FilterDecision(
                    doc_id=str(row["doc_id"]),
                    keep=keep,
                    score=float(row["urd_score"]),
                    reason=f"urd_{self.selection_mode}",
                    metadata={
                        "component_scores": {
                            "utility_score": row["utility_score"],
                            "risk_score": row["risk_score"],
                            "diversity_score": row["diversity_score"],
                            "shift_penalty": row["shift_penalty"],
                            "cost_score": row["cost_score"],
                            "urd_score": row["urd_score"],
                        },
                        "selection_mode": self.selection_mode,
                        "pareto_rank": row.get("pareto_rank"),
                        "disabled_components": sorted(self.disabled_components),
                        "proxy_note": "URD Step 6 smoke selector; effectiveness is not verified.",
                    },
                )
            )
            row["keep"] = keep
        result = self._result(records, decisions)
        self._component_rows = rows
        self._last_records = list(records)
        self._last_result = result
        self._last_runtime_seconds = time.perf_counter() - started
        return result

    def write_outputs(self, output_dir: str | Path, root: Path | None = None) -> dict[str, Any]:
        if self._last_result is None:
            raise ValueError("filter() must be called before write_outputs()")
        root_path = root or Path.cwd()
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        result = self._last_result
        records = self._last_records
        decision_rows = [decision.to_dict() for decision in result.decisions]
        selected_rows = [
            {"doc_id": decision.doc_id, "keep": decision.keep, "score": decision.score, "reason": decision.reason}
            for decision in result.decisions
        ]
        score_rows = [
            {
                "doc_id": decision.doc_id,
                "score": decision.score,
                "component_scores": decision.metadata.get("component_scores", {}),
                "metadata": decision.metadata,
            }
            for decision in result.decisions
        ]
        kept_ids = {decision.doc_id for decision in result.decisions if decision.keep}
        kept_records = [record for record in records if record.doc_id in kept_ids]
        keep_rate_report = {
            "status": "passed",
            "filter_name": result.filter_name,
            "filter_type": result.filter_type,
            "input_docs": result.input_docs,
            "kept_docs": result.kept_docs,
            "input_estimated_tokens": result.input_estimated_tokens,
            "kept_estimated_tokens": result.kept_estimated_tokens,
            "document_keep_rate": result.document_keep_rate,
            "token_keep_rate": result.token_keep_rate,
            "target_keep_rate": self.config.target_keep_rate,
            "target_keep_rate_check": validate_keep_rate(result.document_keep_rate, self.config.target_keep_rate),
            "token_counter_type": self.config.token_counter_type,
            "notes": "Step 6 URD keep-rate report; smoke selection only.",
        }
        proxy_components = ["utility", "risk", "diversity", "shift", "cost"]
        summary = {
            "method_family": "URD-Selector",
            "selection_mode": self.selection_mode,
            "weights": self.weights,
            "disabled_components": sorted(self.disabled_components),
            "proxy_components": proxy_components,
            "level3_main_method_candidate": True,
            "smoke_only": bool(self.config.smoke_only),
            "verified_effectiveness": False,
            "no_model_training_run": True,
            "no_ppl_or_downstream_result_added": True,
            "notes": "Step 6 smoke selector output; effectiveness must be evaluated in later steps.",
        }
        write_jsonl(output / "selected_doc_ids.jsonl", selected_rows)
        write_jsonl(output / "decisions.jsonl", decision_rows)
        write_jsonl(output / "scores.jsonl", score_rows)
        write_jsonl(output / "component_scores.jsonl", self._component_rows)
        write_json(output / "keep_rate_report.json", keep_rate_report)
        write_json(output / "risk_report.json", build_risk_report(records, kept_records))
        write_json(output / "diversity_report.json", build_diversity_report(kept_records))
        write_json(
            output / "cost_report.json",
            build_cost_report(
                runtime_seconds=self._last_runtime_seconds,
                input_docs=result.input_docs,
                kept_docs=result.kept_docs,
                external_dependency_used=False,
            ),
        )
        write_json(output / "urd_summary.json", summary)
        if self.selection_mode == "pareto":
            write_json(output / "pareto_layers.json", self._pareto_payload)
            with (output / "pareto_frontier.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "doc_id",
                        "pareto_rank",
                        "selected",
                        "utility_score",
                        "diversity_score",
                        "risk_score",
                        "shift_penalty",
                        "cost_score",
                        "tie_break_score",
                    ],
                )
                writer.writeheader()
                for row in self._component_rows:
                    writer.writerow(
                        {
                            "doc_id": row["doc_id"],
                            "pareto_rank": row.get("pareto_rank", ""),
                            "selected": row.get("keep", False),
                            "utility_score": row["utility_score"],
                            "diversity_score": row["diversity_score"],
                            "risk_score": row["risk_score"],
                            "shift_penalty": row["shift_penalty"],
                            "cost_score": row["cost_score"],
                            "tie_break_score": row.get("tie_break_score", ""),
                        }
                    )
        output_names = [
            "selected_doc_ids.jsonl",
            "decisions.jsonl",
            "scores.jsonl",
            "component_scores.jsonl",
            "keep_rate_report.json",
            "risk_report.json",
            "diversity_report.json",
            "cost_report.json",
            "urd_summary.json",
        ]
        if self.selection_mode == "pareto":
            output_names.extend(["pareto_frontier.csv", "pareto_layers.json"])
        output_hashes = {
            name: {"path": project_relative(output / name, root_path), "sha256": sha256_file(output / name)}
            for name in output_names
        }
        manifest = create_filter_manifest(
            config=self.config,
            result=result,
            root=root_path,
            output_dir=output,
            output_hashes=output_hashes,
            proxy_used=True,
            external_dependency="",
            external_dependency_available=False,
            implemented_but_not_run=False,
            historical_baseline=False,
            official_reproduction=False,
            notes="Step 6 URD selector smoke output; not main evidence.",
        )
        manifest.update(summary)
        if self.selection_mode == "pareto":
            manifest["pareto_objectives"] = self._pareto_payload.get("objectives", [])
            manifest["pareto_proxy_used"] = True
        write_json(output / "filter_manifest.json", manifest)
        self._last_manifest = manifest
        return manifest
