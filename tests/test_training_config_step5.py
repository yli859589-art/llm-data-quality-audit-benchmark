from __future__ import annotations

import pytest

from training_v2.config import TrainingConfig, load_training_config


def test_smoke_training_config_requires_smoke_only_true() -> None:
    payload = load_training_config("configs/training/smoke_bpe_tiny.yaml").to_dict()
    payload["smoke_only"] = False

    with pytest.raises(ValueError, match="smoke training scope"):
        TrainingConfig.from_mapping(payload)


def test_protocol_training_config_does_not_claim_smoke_or_completed() -> None:
    config = load_training_config("configs/training/small_bpe_protocol.yaml")

    assert config.scope == "main_protocol"
    assert config.smoke_only is False
    assert config.max_steps == 0
    assert config.batch_size == 0


def test_protocol_training_config_rejects_smoke_only_label() -> None:
    payload = load_training_config("configs/training/small_bpe_protocol.yaml").to_dict()
    payload["smoke_only"] = True

    with pytest.raises(ValueError, match="protocol scopes"):
        TrainingConfig.from_mapping(payload)
