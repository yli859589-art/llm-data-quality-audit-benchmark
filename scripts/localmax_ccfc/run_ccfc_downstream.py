from __future__ import annotations

import argparse
import json
from typing import Any

import torch

from ccfc_utils import CCFC_DOWNSTREAM, ROOT, gpt2_tokenizer, iter_jsonl_any, load_config, load_json, rel, status_payload, write_csv, write_json, write_report
from models_v2.config import ModelConfig
from models_v2.decoder_lm import DecoderLM


def _split_paths(dataset_manifest: dict[str, Any], split: str) -> list[str]:
    value = dataset_manifest.get("split_paths", {}).get(split, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value else []


def _load_cloze_examples(dataset_id: str, tokenizer: Any, limit: int) -> list[dict[str, Any]]:
    manifest = load_json(ROOT / "artifacts" / "localmax_v2_data" / dataset_id / "dataset_manifest.json")
    examples = []
    for rel_path in _split_paths(manifest, "test"):
        for row in iter_jsonl_any(ROOT / rel_path):
            ids = tokenizer.encode(str(row.get("text", "")), add_special_tokens=False)
            if len(ids) < 64:
                continue
            prompt = ids[:48]
            target = ids[48:64]
            examples.append({"id": row["id"], "prompt": prompt, "target": target})
            if len(examples) >= limit:
                return examples
    return examples


def _load_model(dataset_id: str, method: str, seed: int, model_cfg: ModelConfig, device: str) -> DecoderLM | None:
    ckpt = ROOT / "artifacts" / "localmax_ccfc_training" / dataset_id / method / f"seed_{seed}" / "final_checkpoint.pt"
    if not ckpt.exists():
        return None
    payload = torch.load(ckpt, map_location="cpu")
    state = payload.get("model_state_dict_fp16")
    if not isinstance(state, dict):
        return None
    model = DecoderLM(model_cfg)
    model.load_state_dict({key: value.to(torch.float32) for key, value in state.items()}, strict=True)
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def _score_cloze(model: DecoderLM, examples: list[dict[str, Any]], device: str) -> dict[str, Any]:
    losses = []
    context = model.config.context_length
    for example in examples:
        ids = (example["prompt"] + example["target"])[:context]
        if len(ids) < 2:
            continue
        x = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
        y = torch.tensor([ids[1:]], dtype=torch.long, device=device)
        _, loss = model(x, y)
        assert loss is not None
        losses.append(float(loss.detach().cpu()))
    if not losses:
        return {"examples_scored": 0, "mean_cloze_nll": "", "mean_cloze_log_ppl": "", "claim_allowed": False}
    mean_loss = sum(losses) / len(losses)
    return {"examples_scored": len(losses), "mean_cloze_nll": mean_loss, "mean_cloze_log_ppl": mean_loss, "claim_allowed": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_ccfc/downstream_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    model_matrix = load_config("configs/localmax_v2/model_matrix.yaml")
    model_cfg = ModelConfig.from_mapping(model_matrix["models"][model_matrix["core_model"]])
    tokenizer = gpt2_tokenizer()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows: list[dict[str, Any]] = []
    blocking: list[str] = []
    datasets = ["openwebtext_v2_100m", "c4_en_v2_100m"]
    seed = int(config["seed_for_downstream"])
    for dataset_id in datasets:
        examples = _load_cloze_examples(dataset_id, tokenizer, int(config["examples_per_benchmark"]))
        for method in config["methods_for_downstream"]:
            model = _load_model(dataset_id, str(method), seed, model_cfg, device)
            if model is None:
                rows.append(
                    {
                        "dataset_id": dataset_id,
                        "method_name": method,
                        "seed": seed,
                        "benchmark": "local_lambada_style_cloze",
                        "status": "missing_checkpoint",
                        "examples_scored": 0,
                        "mean_cloze_nll": "",
                        "mean_cloze_log_ppl": "",
                        "official_full_downstream": False,
                        "claim_allowed": False,
                    }
                )
                continue
            result = _score_cloze(model, examples, device)
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "method_name": method,
                    "seed": seed,
                    "benchmark": "local_lambada_style_cloze",
                    "status": "completed" if result["examples_scored"] else "empty",
                    "examples_scored": result["examples_scored"],
                    "mean_cloze_nll": result["mean_cloze_nll"],
                    "mean_cloze_log_ppl": result["mean_cloze_log_ppl"],
                    "official_full_downstream": False,
                    "claim_allowed": False,
                }
            )
    rows.extend(
        [
            {
                "dataset_id": "all",
                "method_name": "all",
                "seed": seed,
                "benchmark": benchmark,
                "status": "not_run_official_harness_required",
                "examples_scored": 0,
                "mean_cloze_nll": "",
                "mean_cloze_log_ppl": "",
                "official_full_downstream": False,
                "claim_allowed": False,
            }
            for benchmark in ["piqa_subset", "arc_easy_subset"]
        ]
    )
    completed = [row for row in rows if row["status"] == "completed"]
    if not completed:
        blocking.append("No local cloze downstream rows completed; run CCF-C training checkpoints first.")
    CCFC_DOWNSTREAM.mkdir(parents=True, exist_ok=True)
    fields = ["dataset_id", "method_name", "seed", "benchmark", "status", "examples_scored", "mean_cloze_nll", "mean_cloze_log_ppl", "official_full_downstream", "claim_allowed"]
    write_csv(CCFC_DOWNSTREAM / "downstream_subset.csv", fields, rows)
    manifest = {
        "step": "localmax_ccfc_strengthening",
        "scope": "ccfc_downstream",
        "completed": bool(completed),
        "local_downstream_subset": True,
        "official_full_downstream": False,
        "downstream_subset": "artifacts/localmax_ccfc_downstream/downstream_subset.csv",
        "claim_allowed": False,
    }
    write_json(CCFC_DOWNSTREAM / "downstream_manifest.json", manifest)
    ready = bool(completed)
    report = status_payload(
        "downstream",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "CCFC_DOWNSTREAM_LOCAL_PROBE_COMPLETED" if ready else "CCFC_PARTIAL_EVIDENCE",
            "local_downstream_subset": True,
            "official_full_downstream": False,
            "downstream_completed": ready,
            "downstream_rows": len(rows),
            "completed_rows": len(completed),
            "claim_allowed": False,
            "notes": [
                "Local cloze probes are diagnostic only.",
                "No official downstream completion claim is made.",
            ],
        },
    )
    write_report(report, "localmax_ccfc_downstream_report", "LocalMax CCF-C Downstream Probe Report")
    print(json.dumps({"ccfc_downstream_ready": ready, "official_full_downstream": False, "completed_rows": len(completed)}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
