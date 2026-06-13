from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from experiment_utils import root


REQUIRED_FILES = [root / "README.md"]
OPTIONAL_ROOT_FILES = [
    root / "PROJECT_SUMMARY.md",
    root / "PROJECT_ONE_PAGE.md",
    root / "RESUME_BULLETS.md",
    root / "TECHNICAL_OVERVIEW.md",
    root / "DEMO_GUIDE.md",
]
DANGEROUS_PHRASES = [
    "HDQS++ beats raw",
    "HDQS++ outperforms raw",
    "HDQS++ improves LLM pretraining",
    "improved LLM pretraining perplexity",
    "beat raw baseline",
    "developed a state-of-the-art filter",
    "state-of-the-art",
    "SOTA",
    "CCF-C ready",
    "CCF-C-ready project",
    "CCF-B ready",
    "CCF-A ready",
    "full OpenWebText",
    "full C4",
    "large-scale OpenWebText",
    "large-scale C4",
    "web-scale result",
    "beats raw",
    "outperforms raw",
    "URD-Selector verified",
    "URD-Selector beats raw",
    "URD-Selector outperforms raw",
    "URD-Selector improves PPL",
    "URD-Selector improves downstream",
    "Level 3 completed",
    "LEVEL3_COMPLETED_ARTIFACT",
    "500M tokens completed",
    "1B tokens completed",
    "official C4 reproduction",
    "official Gopher reproduction",
    "official CCNet reproduction",
    "medium model completed",
    "large-lite completed",
    "downstream completed",
    "mechanism proved",
    "Pareto frontier improved",
    "publication-ready",
    "large-scale LLM pretraining completed",
    "significant improvement over raw",
    "statistically significant over raw",
    "paper-ready",
    "camera-ready",
    "accepted-level result",
]
SAFE_CONTEXT_MARKERS = [
    "does not claim",
    "does not outperform",
    "do not claim",
    "do not prove",
    "do not rewrite",
    "does not prove",
    "must not be",
    "not claim",
    "not outperform",
    "not a",
    "not be used",
    "not complete",
    "not final",
    "not full",
    "not supported",
    "not ccf-b ready",
    "not ccf-a ready",
    "not ready",
    "not currently",
    "not yet",
    "not completed",
    "not verified",
    "does not mark",
    "future claims allowed only after evidence",
    "future method direction",
    "future target",
    "upgrade target",
    "planned protocol",
    "roadmap, not evidence",
    "forbidden current claims",
    "forbidden current claim",
    "disallowed claim",
    "forbidden until",
    "allowed only after evidence",
    "unsupported",
    "forbidden claim",
    "forbidden claims",
    "forbidden current claim",
    "obsolete false claim",
    "not ccf-c ready",
    "claim boundary",
    "reporting contract",
    "known limitations",
    "remaining work",
    "gap audit",
    "false",
]
ARCHIVAL_CONTEXT_MARKERS = [
    "archival note",
    "future publication note",
    "obsolete false claim",
]
WARNING_CONTEXT_MARKERS = [
    "future",
    "roadmap",
    "planned",
    "before",
    "if supported",
]


@dataclass
class Finding:
    file: str
    line: int
    phrase: str
    classification: str
    context: str
    reason: str


def _normalize(text: str) -> str:
    cleaned = re.sub(r"[*_`>#|]", " ", text.casefold())
    cleaned = cleaned.replace("ccf c", "ccf-c")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    special_patterns = {
        "HDQS++ beats raw": r"HDQS\+\+(?:\s+v\d+)?\s+beats\s+raw",
        "HDQS++ outperforms raw": r"HDQS\+\+(?:\s+v\d+)?\s+outperforms\s+raw",
        "HDQS++ improves LLM pretraining": r"HDQS\+\+(?:\s+v\d+)?\s+improves\s+LLM\s+pretraining",
        "CCF-C ready": r"CCF-C[\s-]+ready",
        "CCF-C-ready project": r"CCF-C[\s-]+ready\s+project",
        "CCF-B ready": r"CCF-B[\s-]+ready",
        "CCF-A ready": r"CCF-A[\s-]+ready",
        "full OpenWebText": r"full\s+OpenWebText",
        "full C4": r"full\s+C4",
        "URD-Selector verified": r"URD-Selector\s+verified",
        "URD-Selector beats raw": r"URD-Selector\s+beats\s+raw",
        "URD-Selector outperforms raw": r"URD-Selector\s+outperforms\s+raw",
        "URD-Selector improves PPL": r"URD-Selector\s+improves\s+PPL",
        "URD-Selector improves downstream": r"URD-Selector\s+improves\s+downstream",
        "Level 3 completed": r"Level\s+3\s+completed",
        "LEVEL3_COMPLETED_ARTIFACT": r"LEVEL3_COMPLETED_ARTIFACT",
        "500M tokens completed": r"500M\s+tokens\s+completed",
        "1B tokens completed": r"1B\s+tokens\s+completed",
        "official C4 reproduction": r"official\s+C4\s+reproduction",
        "official Gopher reproduction": r"official\s+Gopher\s+reproduction",
        "official CCNet reproduction": r"official\s+CCNet\s+reproduction",
        "medium model completed": r"medium\s+model\s+completed",
        "large-lite completed": r"large-lite\s+completed",
        "downstream completed": r"downstream\s+completed",
        "mechanism proved": r"mechanism\s+proved",
        "Pareto frontier improved": r"Pareto\s+frontier\s+improved",
        "large-scale LLM pretraining completed": r"large-scale\s+LLM\s+pretraining\s+completed",
    }
    if phrase == "SOTA":
        return re.compile(r"\bSOTA\b", flags=re.IGNORECASE)
    if phrase in special_patterns:
        return re.compile(special_patterns[phrase], flags=re.IGNORECASE)
    escaped = re.escape(phrase)
    return re.compile(escaped, flags=re.IGNORECASE)


def _scan_files() -> tuple[list[Path], list[str]]:
    docs = sorted((root / "docs").rglob("*.md")) if (root / "docs").exists() else []
    files = [path for path in REQUIRED_FILES if path.exists()]
    files.extend(docs)
    optional_missing = []
    for path in OPTIONAL_ROOT_FILES:
        if path.exists():
            files.append(path)
        else:
            optional_missing.append(path.name)
    unique: list[Path] = []
    seen = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return unique, optional_missing


def _classify(path: Path, context: str) -> tuple[str, str]:
    normalized = _normalize(context)
    relative = path.relative_to(root).as_posix()
    if "future_publication_notes" in relative or any(marker in normalized for marker in ARCHIVAL_CONTEXT_MARKERS):
        return "archival_context", "Phrase appears in archival or future-publication context."
    if any(marker in normalized for marker in SAFE_CONTEXT_MARKERS):
        return "allowed_negative_context", "Phrase appears in a non-claim, forbidden-claim, limitation, or claim-boundary context."
    if any(marker in normalized for marker in WARNING_CONTEXT_MARKERS):
        return "warning_context", "Phrase appears in future/planned context and should be reviewed before public release."
    return "unsafe_claim", "Phrase appears without an allowed negative, archival, or warning context."


def _line_context(lines: list[str], index: int) -> str:
    start = max(0, index - 10)
    end = min(len(lines), index + 5)
    return " ".join(line.strip() for line in lines[start:end])


def scan() -> dict[str, object]:
    files, optional_missing = _scan_files()
    findings: list[Finding] = []
    for path in files:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            for phrase in DANGEROUS_PHRASES:
                if _phrase_pattern(phrase).search(line):
                    context = _line_context(lines, index)
                    classification, reason = _classify(path, context)
                    findings.append(
                        Finding(
                            file=path.relative_to(root).as_posix(),
                            line=index + 1,
                            phrase=phrase,
                            classification=classification,
                            context=context,
                            reason=reason,
                        )
                    )
    unsafe = [finding for finding in findings if finding.classification == "unsafe_claim"]
    allowed = [
        finding
        for finding in findings
        if finding.classification in {"allowed_negative_context", "archival_context", "warning_context"}
    ]
    return {
        "status": "failed" if unsafe else "passed",
        "scanned_files": [path.relative_to(root).as_posix() for path in files],
        "optional_files_not_present": optional_missing,
        "flagged_phrases": [asdict(finding) for finding in findings],
        "allowed_exceptions": [asdict(finding) for finding in allowed],
        "unsafe_claims": [asdict(finding) for finding in unsafe],
        "summary": {
            "scanned_file_count": len(files),
            "optional_not_present_count": len(optional_missing),
            "flagged_phrase_count": len(findings),
            "unsafe_claim_count": len(unsafe),
            "allowed_exception_count": len(allowed),
        },
    }


def _write_markdown(report: dict[str, object], path: Path) -> None:
    flagged = report["flagged_phrases"]
    assert isinstance(flagged, list)
    lines = [
        "# Claim Hygiene Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Scanned files: `{report['summary']['scanned_file_count']}`",  # type: ignore[index]
        f"- Optional files not present: `{report['summary']['optional_not_present_count']}`",  # type: ignore[index]
        f"- Flagged phrases: `{report['summary']['flagged_phrase_count']}`",  # type: ignore[index]
        f"- Unsafe claims: `{report['summary']['unsafe_claim_count']}`",  # type: ignore[index]
        "",
        "## Optional Files Not Present",
        "",
    ]
    optional = report["optional_files_not_present"]
    assert isinstance(optional, list)
    lines.extend([f"- `{name}`: `not_present`" for name in optional] or ["- None"])
    lines.extend(
        [
            "",
            "## Flagged Phrases",
            "",
            "| File | Line | Phrase | Classification | Reason |",
            "|---|---:|---|---|---|",
        ]
    )
    for item in flagged:
        assert isinstance(item, dict)
        reason = str(item["reason"]).replace("|", "\\|")
        lines.append(
            f"| `{item['file']}` | {item['line']} | `{item['phrase']}` | "
            f"`{item['classification']}` | {reason} |"
        )
    if not flagged:
        lines.append("|  |  |  |  | No dangerous phrases found. |")
    lines.extend(
        [
            "",
            "## Pass/Fail Rule",
            "",
            "The check fails only for `unsafe_claim`. Phrases in explicit forbidden-claim, non-claim, limitation, claim-boundary, or archival contexts are retained as allowed exceptions.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    report = scan()
    output_dir = root / "artifacts" / "release"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "claim_hygiene_report.json"
    md_path = output_dir / "claim_hygiene_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    _write_markdown(report, md_path)
    print(f"Claim hygiene: {report['status']}")
    print(f"Report: {json_path.relative_to(root).as_posix()}")
    if report["status"] != "passed":
        raise SystemExit("Claim hygiene failed; see artifacts/release/claim_hygiene_report.md")


if __name__ == "__main__":
    main()
