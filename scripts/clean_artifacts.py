from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_CACHE_NAMES = {".coverage", "coverage.xml", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEMP_BENCHMARK_PREFIXES = (
    "artifacts/llm_benchmark_ci",
    "artifacts/llm_benchmark_quick",
    "artifacts/llm_benchmark_long_probe",
)


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def clean_generated_paths(
    root: str | Path,
    *,
    include_temp_benchmarks: bool = False,
    dry_run: bool = False,
) -> list[str]:
    """Remove generated cache files without deleting official experiment artifacts."""
    root_path = Path(root).resolve()
    removed: list[str] = []
    targets: list[Path] = []
    for path in root_path.rglob("*"):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root_path).as_posix()
        is_cache = (
            path.name in DEFAULT_CACHE_NAMES
            or "__pycache__" in path.parts
            or path.suffix == ".pyc"
        )
        is_temp_benchmark = include_temp_benchmarks and any(
            relative.startswith(prefix) for prefix in TEMP_BENCHMARK_PREFIXES
        )
        if is_cache or is_temp_benchmark:
            targets.append(path)

    for target in sorted(targets, key=lambda item: len(item.parts), reverse=True):
        resolved = target.resolve()
        if not _is_within(resolved, root_path):
            raise RuntimeError(f"Refusing to remove outside repository root: {resolved}")
        if not target.exists():
            continue
        removed.append(target.relative_to(root_path).as_posix())
        if dry_run:
            continue
        if target.is_dir():
            for child in sorted(target.rglob("*"), key=lambda item: len(item.parts), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            target.rmdir()
        else:
            target.unlink()
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--include-temp-benchmarks", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    removed = clean_generated_paths(
        args.root,
        include_temp_benchmarks=args.include_temp_benchmarks,
        dry_run=args.dry_run,
    )
    action = "Would remove" if args.dry_run else "Removed"
    print(f"{action} {len(removed)} generated cache/temp paths.")
    for path in removed[:25]:
        print(path)


if __name__ == "__main__":
    main()
