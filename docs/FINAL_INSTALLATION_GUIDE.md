# Final installation and operation guide

## Windows PowerShell

```powershell
git clone <repository-url>
cd llm-data-quality-audit-benchmark
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[data,tokenizers,ui]"
python scripts/quality_system.py --help
streamlit run apps/quality_system_app.py --server.address 127.0.0.1
```

The UI listens only on `127.0.0.1`.  It does not download corpora or models at
startup.  If Streamlit is intentionally omitted, install the core package with
`pip install -e ".[data,tokenizers]"` and use the CLI.

## First usable flow without formal corpora

Use a clearly labelled local JSONL/JSONL.GZ/Parquet file, then run:

```powershell
python scripts/quality_system.py import fixture C:\data\fixture.jsonl --source local_fixture
python scripts/quality_system.py analyze fixture --sample-limit 10000
python scripts/quality_system.py run fixture raw --task-id fixture-raw
python scripts/quality_system.py status fixture-raw
python scripts/quality_system.py export fixture-raw
```

All generated catalog, task state, output shards, reports and exports are under
`artifacts/p2_01_system/`.  Formal historical results are not overwritten.

## Formal data restoration

The release contains no C4/OpenWebText raw shards or model weights.  Use the
declared source/version and expected SHA-256 from the historical manifests, or
register a distinct new dataset version.  Do not copy a different source over a
historical shard path to force a hash match.  `scripts/fetch_p1_02_shard.py`
creates a no-network plan by default and requires explicit `--execute`.
