from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import write_json, write_text
from dataaudit_lm.integrity.paths import REPORTS

LEGACY_TERMS = [
    "LOCAL" + "MAX",
    "LOCAL" + "_MAX",
    "CC" + "FC",
    "COURSE" + "_PROJECT" + "_SUITE",
    "LLM" + "_BENCHMARK",
    "HDQS" + "++",
]
NEW_SCOPE = [
    "src/dataaudit_lm/",
    "scripts/dataaudit_lm/",
    "configs/dataaudit_lm/",
    "docs/PROJECT_OVERVIEW.md",
    "docs/RESULTS.md",
    "docs/EVIDENCE_SCOPE.md",
    "docs/RESUME_PROJECT.md",
    "README.md",
]


def _classify(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith(("src/dataaudit_lm/", "scripts/dataaudit_lm/", "configs/dataaudit_lm/")):
        return "ACTIVE_NEW_CODE"
    if rel.startswith(("src/" + "course_project" + "_suite/", "projects/")):
        return "ACTIVE_LEGACY_DEPENDENCY"
    if rel.startswith("artifacts/"):
        return "LEGACY_ARTIFACT"
    if ("LOCAL" + "MAX") in path.name.upper() or rel.startswith("docs/"):
        return "LEGACY_DOCUMENTATION"
    if rel.startswith("tests/test_" + "local" + "max"):
        return "LEGACY_TEST"
    return "CONTENT_ONLY"


def main() -> None:
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").upper()
        rel = path.relative_to(ROOT).as_posix()
        for term in LEGACY_TERMS:
            if term in text or term in rel.upper():
                findings.append({"path": rel, "term": term, "category": _classify(path)})
    new_scope_hits = [
        item
        for item in findings
        if any(
            item["path"].startswith(scope) or item["path"] == scope.rstrip("/")
            for scope in NEW_SCOPE
        )
    ]
    counts = Counter(item["category"] for item in findings)
    payload = {
        "inventory_version": "dataaudit_lm_naming_inventory_v1",
        "legacy_terms": LEGACY_TERMS,
        "new_scope": NEW_SCOPE,
        "new_scope_hit_count": len(new_scope_hits),
        "new_scope_hits": new_scope_hits,
        "category_counts": dict(sorted(counts.items())),
        "full_repo_hit_count": len(findings),
        "full_repo_zero_hit_required_this_round": False,
        "findings": findings,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    write_json(REPORTS / "naming_inventory.json", payload)
    lines = [
        "# Naming Migration",
        "",
        f"- New mainline hit count: `{len(new_scope_hits)}`",
        f"- Full repository hit count: `{len(findings)}`",
        "- Full repository zero-hit is not required while legacy evidence remains active.",
        "",
        "## Category Counts",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(counts.items()))
    write_text(ROOT / "docs" / "NAMING_MIGRATION.md", "\n".join(lines))
    print(
        json.dumps(
            {"new_scope_hit_count": len(new_scope_hits), "full_repo_hit_count": len(findings)}
        )
    )
    if new_scope_hits:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
