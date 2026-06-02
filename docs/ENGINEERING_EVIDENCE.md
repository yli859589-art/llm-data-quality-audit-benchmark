# Engineering Evidence

## Local repository evidence

- Local Git repository initialized on branch `main`.
- Initial focused-project commit: `ceddde9ecc2686461292fb6f9685ad4c922dbca7`
- Release version: `3.0.0`
- Release tag: `v3.0.0`
- GitHub Actions workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Measured coverage: [`docs/COVERAGE_REPORT.txt`](COVERAGE_REPORT.txt)

The local machine did not provide a system `git` executable. Standard `.git` metadata was created with the Python `dulwich` Git implementation. Install Git or GitHub Desktop before publishing the repository.

## Workflow evidence

The included GitHub Actions workflow installs runtime and development dependencies, runs a coverage-instrumented quick focused benchmark, executes the full unit-test suite, validates repository structure, and compiles Python sources.

## Evidence that requires publication

The following items cannot be generated honestly without a GitHub repository and account authorization:

- GitHub repository URL.
- Online Actions run URL and live status badge.
- Pull-request review history.
- Remote release page.

After publishing, replace the static CI workflow badge in `README.md` with the repository's live Actions badge and record the first successful run URL here.

## Release checklist

```bash
git status
git log --oneline --decorate --graph
git remote add origin <your-github-repository-url>
git push -u origin main --tags
```
