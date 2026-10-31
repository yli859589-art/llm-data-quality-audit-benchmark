from __future__ import annotations

import sys
from pathlib import Path

import torch

from training_v2.checkpoint import FULL_STATE_FORMAT, load_training_state, save_full_training_state
from training_v2.sampling import build_document_token_pool


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "localmax_ccfc"))
import run_ccfc_filters  # noqa: E402
import run_ccfc_downstream  # noqa: E402


def _encode(text: str) -> list[int]:
    return [int(token) for token in text.split()]


def test_streamed_sampler_scans_full_pool_and_is_input_order_independent() -> None:
    records = [
        {"id": "a", "text": "1 1 1", "gpt2_tokens": 3},
        {"id": "b", "text": "2 2 2", "gpt2_tokens": 3},
        {"id": "c", "text": "3 3 3", "gpt2_tokens": 3},
        {"id": "d", "text": "4 4 4", "gpt2_tokens": 3},
    ]
    forward, audit_a = build_document_token_pool(lambda: iter(records), _encode, token_budget=6, seed=17)
    reverse, audit_b = build_document_token_pool(lambda: iter(list(reversed(records))), _encode, token_budget=6, seed=17)
    assert audit_a["source_pool_documents"] == 4
    assert audit_a["selected_document_ids"] == audit_b["selected_document_ids"]
    assert forward == reverse
    assert audit_a["input_order_independent"] is True


def test_full_checkpoint_restores_optimizer_model_and_progress_exactly(tmp_path: Path) -> None:
    torch.manual_seed(3)
    first = torch.nn.Linear(2, 1)
    optimizer = torch.optim.AdamW(first.parameters(), lr=0.01)
    x, y = torch.tensor([[1.0, 2.0]]), torch.tensor([[1.0]])

    def step(model: torch.nn.Module, opt: torch.optim.Optimizer) -> float:
        loss = ((model(x) - y) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        return float(loss.detach())

    step(first, optimizer); step(first, optimizer)
    saved = save_full_training_state(model=first, optimizer=optimizer, path=tmp_path / "state.pt", step=2, tokens_seen=8, sampler_state={"cursor": 2}, model_config={"name": "tiny"}, training_config={"seed": 3}, data_manifest_hash="abc", data_version="fixture-v1")
    reference_loss = step(first, optimizer)
    reference = {key: value.detach().clone() for key, value in first.state_dict().items()}
    resumed = torch.nn.Linear(2, 1)
    resumed_optimizer = torch.optim.AdamW(resumed.parameters(), lr=0.01)
    state = load_training_state(model=resumed, optimizer=resumed_optimizer, path=tmp_path / "state.pt")
    resumed_loss = step(resumed, resumed_optimizer)
    assert saved["checkpoint_format_version"] == FULL_STATE_FORMAT
    assert state == {**state, "resume_capability": "exact_resume", "step": 2, "tokens_seen": 8, "sampler_state": {"cursor": 2}, "data_manifest_hash": "abc", "data_version": "fixture-v1"}
    assert resumed_loss == reference_loss
    for key, value in reference.items():
        assert torch.equal(value, resumed.state_dict()[key])


def test_legacy_checkpoint_is_explicitly_weights_only(tmp_path: Path) -> None:
    model = torch.nn.Linear(1, 1)
    legacy = tmp_path / "legacy.pt"
    torch.save({"model_state_dict": model.state_dict()}, legacy)
    result = load_training_state(model=torch.nn.Linear(1, 1), optimizer=torch.optim.AdamW(torch.nn.Linear(1, 1).parameters()), path=legacy)
    assert result["resume_capability"] == "weights_only_initialization"
    assert result["tokens_seen"] == 0


def test_random_control_matches_token_budget_not_document_count() -> None:
    docs = [{"id": str(index), "text": "x", "gpt2_tokens": count} for index, count in enumerate([4, 5, 6, 7])]
    config = {"length_filter": {"min_gpt2_tokens": 5, "max_gpt2_tokens": 6}, "random_same_keep_rate": {"seed": 9, "match_mode": "token_budget", "token_budget_tolerance": 0}}
    rows = run_ccfc_filters._decisions("fixture", "random_same_keep_rate", docs, config)
    assert sum(row["gpt2_tokens"] for row in rows if row["keep"]) == 11
    assert all(row["random_match_mode"] == "token_budget" for row in rows)


def test_cloze_excludes_prompt_loss() -> None:
    class Model:
        class config:
            context_length = 8

        def __call__(self, x: torch.Tensor, _labels: None):
            logits = torch.full((1, x.size(1), 2), -20.0)
            logits[:, 0, 1] = 20.0  # deliberately wrong for the prompt label 0
            logits[:, 1:, 1] = 20.0  # correct target labels 1
            return logits, None

    result = run_ccfc_downstream._score_cloze(Model(), [{"id": "x", "prompt": [0, 0], "target": [1, 1]}], "cpu")
    assert result["examples_scored"] == 1
    assert float(result["mean_cloze_nll"]) < 1e-5
