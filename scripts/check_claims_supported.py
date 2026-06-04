from __future__ import annotations

from experiment_utils import root

FORBIDDEN_CLAIMS = [
    "CCF-C ready",
    "CCF_C_EXPERIMENT_READY",
    "statistically significant improvement",
    "beats all baselines",
    "state-of-the-art",
    "paper-ready results",
    "official CMU course project",
    "Carnegie Mellon University competition",
]


def main() -> None:
    claim_map = root / "docs" / "CLAIM_ARTIFACT_MAP.md"
    if not claim_map.exists():
        raise SystemExit("Missing docs/CLAIM_ARTIFACT_MAP.md")
    text = claim_map.read_text(encoding="utf-8")
    for phrase in ["Claim", "Artifact", "Support level", "Unsupported"]:
        if phrase not in text:
            raise SystemExit(f"Claim map missing required phrase: {phrase}")

    scan_files = [
        root / "README.md",
        root / "docs" / "RESUME.md",
        root / "docs" / "PAPER_DRAFT.md",
    ]
    errors = []
    for path in scan_files:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for claim in FORBIDDEN_CLAIMS:
            if claim.casefold() in content.casefold():
                errors.append(f"{path.relative_to(root)} contains unsupported claim: {claim}")
    if errors:
        raise SystemExit("Claim support check failed." + "\n" + "\n".join(errors))
    print("Claim support check: ok")


if __name__ == "__main__":
    main()
