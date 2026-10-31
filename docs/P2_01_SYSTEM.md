# P2-1 unified local system

`quality_system` is the single P2-1 business layer.  Both the CLI and the
Streamlit UI call `QualitySystemService`; neither has a duplicate filter or data
processing engine.  It reuses `data.scalable_pipeline` for Raw streaming runs
and `filters_v2` for existing filters.  Outputs, dataset catalog, task state,
logs, reports, and exports are isolated under `artifacts/p2_01_system/`.

## Install and run on Windows PowerShell

```powershell
pip install -e ".[data,tokenizers,ui]"
python scripts/quality_system.py --help
streamlit run apps/quality_system_app.py --server.address 127.0.0.1
```

`ui` is optional.  Without it, all core operations remain available through the
CLI.  The Streamlit command binds only to localhost and never downloads a model
or corpus at startup.

## CLI examples

```powershell
python scripts/quality_system.py check C:\data\sample.jsonl
python scripts/quality_system.py import demo C:\data\sample.jsonl --source local
python scripts/quality_system.py analyze demo --sample-limit 10000
python scripts/quality_system.py config-save demo-raw '{"dataset_id":"demo","strategy":"raw","max_documents":100000}'
python scripts/quality_system.py run demo raw --task-id demo-raw
python scripts/quality_system.py status demo-raw
python scripts/quality_system.py export demo-raw
python scripts/quality_system.py evaluate-smoke artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json
```

The `run` command starts a detached local Python worker.  Its status persists in
`tasks.sqlite`, and Raw processing delegates to the P1-2 resumable pipeline.
Other existing batch filters have an explicit `--max-documents` bound in this
system entry point; this prevents accidental unbounded RAM use and does not
claim that those legacy batch algorithms are streaming.

`preflight --mode metadata` invokes the existing protected P0 preflight and
writes only a new P2-1 report.  `config-save` and `config-load` validate the
same configuration schema used by CLI, UI, and worker before storing it.
`evaluate-smoke` is an explicit user action that calls the existing Step 7 LM
smoke evaluator and writes a new P2-1 result; it never re-labels smoke metrics
as a full training result.

## P2-1 local verification

The automated fixture flow imports three marked test records, runs actual
inspection and bounded quality analysis, invokes `exact_dedup`, writes the
actual filtered JSONL and audit outputs, persists/reopens task state, and exports
the completed run as ZIP.  A separate Raw fixture task invokes the P1-2
resumable streaming pipeline.  The existing LM smoke evaluator was also invoked
through this service; its output remains explicitly `main_evidence: false`.

## Evidence and limits

The overview deliberately distinguishes historical manifest token totals from
available source files.  The C4 and OpenWebText manifests are present but their
nine declared shards are absent, so the interface displays the required warning
and cannot claim a complete real-corpus run.  Quality analysis labels bounded
analysis as a prefix sample, language information as a heuristic signal, proxy
filters as proxies, and unrun model evaluation as `未运行`.
