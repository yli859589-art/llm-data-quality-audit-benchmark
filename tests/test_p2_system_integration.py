from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from quality_system.service import QualitySystemService


def _fixture(path: Path) -> None:
    rows = [
        {"id": "a", "text": "A useful English document with enough words.", "split": "train"},
        {"id": "b", "text": "A useful English document with enough words.", "split": "valid"},
        {"id": "c", "text": "<html>noise</html> https://example.test", "split": "test"},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_end_to_end_import_analysis_filter_export_and_persistent_status(tmp_path: Path) -> None:
    source = tmp_path / "fixture.jsonl"
    _fixture(source)
    service = QualitySystemService(tmp_path)
    dataset = service.import_dataset("fixture", source, source="test_fixture")
    assert dataset["documents"] == 3 and dataset["sha256"]
    analysis = service.analyze("fixture", sample_limit=2)
    assert analysis["sample_documents"] == 2 and analysis["duplicate_rows_in_sample"] == 1
    task = service.create_task(
        {
            "task_id": "dedup",
            "dataset_id": "fixture",
            "strategy": "exact_dedup",
            "target_keep_rate": 1.0,
            "max_documents": 10,
            "allow_proxy": True,
        }
    )
    completed = service.execute_task(task["task_id"])
    assert completed["status"] == "completed" and completed["result"]["kept_docs"] == 2
    assert Path(completed["result"]["filtered_dataset"]).is_file()
    assert QualitySystemService(tmp_path).task("dedup")["status"] == "completed"
    archive = service.export_task("dedup")
    assert (
        archive.is_file() and archive.parent == tmp_path / "artifacts" / "p2_01_system" / "exports"
    )
    assert Path(completed["log_path"]).read_text(encoding="utf-8").endswith("completed\n")


def test_streaming_raw_task_uses_p1_pipeline_and_reports_error_without_fake_success(
    tmp_path: Path,
) -> None:
    source = tmp_path / "fixture.jsonl"
    _fixture(source)
    service = QualitySystemService(tmp_path)
    service.import_dataset("fixture", source)
    raw = service.execute_task(
        service.create_task(
            {
                "task_id": "raw",
                "dataset_id": "fixture",
                "strategy": "raw",
                "batch_size": 1,
                "max_documents": 10,
            }
        )["task_id"]
    )
    assert raw["status"] == "completed" and raw["result"]["mode"] == "streaming_raw"
    assert Path(raw["result"]["manifest"]).is_file()
    failed = service.execute_task(
        service.create_task(
            {"task_id": "missing", "dataset_id": "not-imported", "strategy": "raw"}
        )["task_id"]
    )
    assert failed["status"] == "failed" and "unknown dataset" in failed["error"]


def test_validation_path_isolation_and_cli_share_service_logic(tmp_path: Path) -> None:
    source = tmp_path / "fixture.jsonl"
    _fixture(source)
    service = QualitySystemService(tmp_path)
    with pytest.raises(ValueError):
        service.import_dataset("bad/id", source)
    with pytest.raises(ValueError):
        service.validate_filter_config({"dataset_id": "ok", "strategy": "not-a-filter"})
    project_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        str(project_root / "scripts" / "quality_system.py"),
        "--root",
        str(tmp_path),
        "import",
        "cli-fixture",
        str(source),
    ]
    payload = json.loads(subprocess.check_output(command, text=True, cwd=project_root))
    assert payload["dataset_id"] == "cli-fixture"
    assert service.dataset("cli-fixture")["documents"] == 3
    config = {"dataset_id": "cli-fixture", "strategy": "raw", "max_documents": 3}
    assert service.save_config("raw", config).is_file()
    assert service.load_config("raw") == config
    app_source = (project_root / "apps" / "quality_system_app.py").read_text(encoding="utf-8")
    assert "QualitySystemService" in app_source and "service.start_task" in app_source


def test_historical_manifest_only_status_is_explicit_and_no_output_escapes_versioned_root(
    tmp_path: Path,
) -> None:
    service = QualitySystemService(tmp_path)
    status = service.historical_data_status()
    assert all(item["status"] == "manifest_only_missing_source_files" for item in status)
    with pytest.raises(ValueError):
        service._inside_output(tmp_path / "outside")


def test_existing_lm_smoke_evaluator_is_invoked_and_remains_smoke_only(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.json"
    metrics.write_text(
        json.dumps({"tokens_seen": 12, "validation_loss": 2.0, "validation_ppl": 7.4}),
        encoding="utf-8",
    )
    training = tmp_path / "training.json"
    training.write_text(
        json.dumps({"scope": "smoke", "metrics_path": "metrics.json"}), encoding="utf-8"
    )
    result = QualitySystemService(tmp_path).evaluate_smoke_training("training.json", name="lm")
    assert result["smoke_only"] is True
    assert result["metrics"]["main_evidence"] is False
    assert Path(result["output_paths"]["manifest"]).is_file()
