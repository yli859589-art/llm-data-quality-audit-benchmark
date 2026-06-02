from pathlib import Path

root = Path(__file__).resolve().parents[1]
py_files = [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]
source_files = [p for p in (root / "src").rglob("*.py")]
project_readmes = list((root / "projects").glob("*/README.md"))
loc = 0
for p in py_files:
    loc += sum(
        1
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
print(
    {
        "python_files": len(py_files),
        "source_modules": len(source_files),
        "project_families": len(project_readmes),
        "non_blank_non_comment_python_loc": loc,
    }
)
