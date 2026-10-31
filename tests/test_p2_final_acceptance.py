from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
import torch
from torch import nn

from filters_v2.persistent_minhash import PersistentMinHashIndex
from scripts.audit_historical_integrity import audit
from training_v2.checkpoint import load_training_state, save_full_training_state


def _step(
    model: nn.Module, optimizer: torch.optim.Optimizer, x: torch.Tensor, y: torch.Tensor
) -> None:
    optimizer.zero_grad()
    loss = torch.nn.functional.mse_loss(model(x), y)
    loss.backward()
    optimizer.step()


def test_interrupted_training_matches_continuous_training_on_cpu(tmp_path: Path) -> None:
    torch.manual_seed(101)
    random.seed(101)
    initial = nn.Sequential(nn.Linear(2, 4), nn.Dropout(0.25), nn.Linear(4, 1))
    initial_state = {key: value.detach().clone() for key, value in initial.state_dict().items()}
    x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    y = torch.tensor([[1.0], [0.0]])
    torch.manual_seed(202)
    continuous = nn.Sequential(nn.Linear(2, 4), nn.Dropout(0.25), nn.Linear(4, 1))
    continuous.load_state_dict(initial_state)
    continuous_optimizer = torch.optim.Adam(continuous.parameters(), lr=0.01)
    _step(continuous, continuous_optimizer, x, y)
    _step(continuous, continuous_optimizer, x, y)
    torch.manual_seed(202)
    interrupted = nn.Sequential(nn.Linear(2, 4), nn.Dropout(0.25), nn.Linear(4, 1))
    interrupted.load_state_dict(initial_state)
    interrupted_optimizer = torch.optim.Adam(interrupted.parameters(), lr=0.01)
    _step(interrupted, interrupted_optimizer, x, y)
    checkpoint = tmp_path / "resume.pt"
    save_full_training_state(
        model=interrupted,
        optimizer=interrupted_optimizer,
        path=checkpoint,
        step=1,
        tokens_seen=4,
        sampler_state={"cursor": 1},
        model_config={},
        training_config={},
        data_manifest_hash="fixture",
        data_version="fixture-v1",
    )
    resumed = nn.Sequential(nn.Linear(2, 4), nn.Dropout(0.25), nn.Linear(4, 1))
    resumed_optimizer = torch.optim.Adam(resumed.parameters(), lr=0.01)
    restored = load_training_state(model=resumed, optimizer=resumed_optimizer, path=checkpoint)
    _step(resumed, resumed_optimizer, x, y)
    assert restored["resume_capability"] == "exact_resume"
    for name, expected in continuous.state_dict().items():
        assert torch.equal(expected, resumed.state_dict()[name]), name


def test_persistent_minhash_reuses_signature_and_preserves_cluster_choice(tmp_path: Path) -> None:
    index = PersistentMinHashIndex(
        tmp_path / "index.sqlite", shingle_size=2, permutations=32, bands=8
    )
    text = "duplicate content with sufficient token variety for exact shingles"
    index.add_and_cluster("z", text, "train", threshold=0.9)
    index.add_and_cluster("a", text, "valid", threshold=0.9)
    index.commit()
    assert index.cluster_representatives() == {"a": "a", "z": "a"}
    assert index.profile_snapshot()["confirmed_comparisons"] >= 1
    index.close()


def test_legacy_integrity_audit_is_read_only_and_reports_mismatch(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.json"
    metrics.write_text("{}", encoding="utf-8")
    report = tmp_path / "report.md"
    report.write_text("report", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "metrics_path": "metrics.json",
                "metrics_hash": "0" * 64,
                "report_path": "report.md",
                "report_hash": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    before = metrics.read_bytes(), report.read_bytes(), manifest.read_bytes()
    result = audit(tmp_path, manifest)
    assert result["status"] == "fail" and all(not item["match"] for item in result["findings"])
    assert before == (metrics.read_bytes(), report.read_bytes(), manifest.read_bytes())


def test_integrity_audit_requires_existing_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        audit(tmp_path, tmp_path / "missing.json")
