# Legacy Scope

This repository contains both the current LLM data-quality audit benchmark and
older educational assets. Step 1 keeps those assets, but makes their role clear.

## Legacy Educational Assets

The following areas are educational or archival assets, not the Level 3
DataAudit-LM mainline:

- `course_project_suite`
- `projects/cs188`
- `projects/cs224n`
- `projects/cs231n`
- `projects/cs336`
- `projects/d2l`
- `projects/coursera_ml`
- related legacy notebooks, examples, and smoke artifacts

Some of these paths may live under `src/course_project_suite/` rather than a
top-level `projects/` directory. The policy applies to the asset family, not
only a single path spelling.

## Why They Should Not Be Deleted Now

These assets may still contain:

- useful tests;
- algorithm implementations;
- examples that protect packaging assumptions;
- historical context for the original project suite;
- code that existing checks still import.

Deleting them during the research upgrade would create unnecessary risk. The
better approach is to isolate them from public research claims.

## How They Should Be Described

Safe wording:

> Legacy educational implementation assets are preserved for historical,
> testing, and portfolio context, but they are not part of the DataAudit-LM
> Level 3 research mainline.

Unsafe wording:

> The legacy course suite is evidence that the current data-filtering benchmark
> is a completed CCF-B research project.

The unsafe sentence is a forbidden-claim example only.

## Future Isolation Strategy

Future refactoring may:

- move legacy code into a clearly named legacy namespace;
- remove legacy docs from the main README navigation;
- keep tests that still protect shared utilities;
- mark educational artifacts as archival in the artifact index;
- keep public claims focused on DataAudit-LM.

Future refactoring must not delete tests, results, or negative evidence merely
to make the repository look cleaner.

## Boundary for Citations and Resume Use

When citing this repository, mention the legacy course assets only as archived
educational material. Do not blend them into the research contribution.

The main research contribution is the data-quality audit benchmark, claim
hygiene, artifact lineage, and future Level 3 upgrade path.
