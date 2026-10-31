from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight_project.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def make_repo(root: Path, *, shards: bool = False, source: str = "example/real-corpus") -> Path:
    for name in ("src", "scripts", "configs", "tests", "artifacts", "data"):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n', encoding="utf-8")
    (root / "requirements.txt").write_text("numpy\n", encoding="utf-8")
    (root / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")
    for dataset in ("c4_en_v2_100m", "openwebtext_v2_100m"):
        directory = root / "artifacts" / "localmax_v2_data" / dataset
        directory.mkdir(parents=True)
        rel = f"artifacts/localmax_v2_data/{dataset}/shards/train-0000.jsonl.gz"
        manifest = {"dataset_id": dataset, "dataset_name": dataset, "source": source, "source_version": "pinned-test", "document_count": 1, "actual_gpt2_tokens": 3, "fallback_used": False, "split_paths": {"train": rel, "valid": [], "test": []}, "split_gpt2_tokens": {"train": 3, "valid": 0, "test": 0}, "split_document_counts": {"train": 1, "valid": 0, "test": 0}, "data_hashes": f"artifacts/localmax_v2_data/{dataset}/data_hashes.json"}
        if shards:
            shard = root / rel
            shard.parent.mkdir(parents=True)
            with gzip.open(shard, "wt", encoding="utf-8") as handle:
                handle.write('{"id":"1","text":"real corpus text","gpt2_tokens":3}\n')
            train_hash = digest(shard)
        else:
            train_hash = "0" * 64
        (directory / "data_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (directory / "data_hashes.json").write_text(json.dumps({"split_sha256": {"train": train_hash, "valid": {}, "test": {}}}), encoding="utf-8")
    (root / "artifacts" / "historical.csv").write_text("metric,value\nloss,1\n", encoding="utf-8")
    return root


def run(root: Path, mode: str, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    output = root / f"{mode}.json"
    completed = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--mode", mode, "--output", str(output), *args], capture_output=True, text=True, check=False)
    return completed, json.loads(output.read_text(encoding="utf-8"))


def test_metadata_reports_missing_shards_without_claiming_successful_full_data(tmp_path: Path) -> None:
    completed, payload = run(make_repo(tmp_path), "metadata")
    assert completed.returncode == 0
    assert any(entry["id"].endswith(".shards") and entry["status"] == "warn" for entry in payload["checks"])


def test_full_fails_for_missing_real_shards(tmp_path: Path) -> None:
    completed, payload = run(make_repo(tmp_path), "full")
    assert completed.returncode == 1 and payload["overall_status"] == "fail"


def test_full_passes_hashes_then_rejects_corruption(tmp_path: Path) -> None:
    root = make_repo(tmp_path, shards=True)
    completed, payload = run(root, "full")
    assert completed.returncode == 0, completed.stderr
    next((root / "artifacts").rglob("*.gz")).write_bytes(b"corrupt")
    completed, payload = run(root, "full")
    assert completed.returncode == 1
    assert any(entry["id"].endswith(".shard_hashes") and entry["status"] == "fail" for entry in payload["checks"])


def test_full_rejects_synthetic_fallback_source(tmp_path: Path) -> None:
    completed, payload = run(make_repo(tmp_path, shards=True, source="fixture/synthetic-corpus"), "full")
    assert completed.returncode == 1
    assert any(entry["id"].endswith(".no_synthetic_fallback") and entry["status"] == "fail" for entry in payload["checks"])


def test_baseline_detects_historical_mutation_and_writes_traceable_report(tmp_path: Path) -> None:
    root = make_repo(tmp_path, shards=True)
    baseline = root / "baseline.json"
    completed, _ = run(root, "metadata", "--baseline-manifest", str(baseline), "--write-baseline")
    assert completed.returncode == 0 and baseline.exists()
    (root / "artifacts" / "historical.csv").write_text("metric,value\nloss,2\n", encoding="utf-8")
    completed, payload = run(root, "metadata", "--baseline-manifest", str(baseline))
    assert completed.returncode == 1
    assert next(entry for entry in payload["checks"] if entry["id"] == "baseline_snapshot")["status"] == "fail"
