.PHONY: install check claim-hygiene minimal-benchmark audit-benchmark tables figures dashboard release-check clean-cache

install:
	python -m pip install -r requirements.txt
	python -m pip install -r requirements-dev.txt
	python -m pip install -e .

check:
	python scripts/run_all_checks.py --timeout 300

claim-hygiene:
	python scripts/check_claim_hygiene.py

minimal-benchmark:
	python scripts/run_minimal_benchmark.py --quick-check

audit-benchmark:
	python scripts/run_audit_benchmark.py --skip-training

tables:
	python scripts/generate_tables.py

figures:
	python scripts/generate_figures.py

dashboard:
	python scripts/generate_project_dashboard.py

release-check:
	python scripts/run_release_checks.py --timeout 300

clean-cache:
	python scripts/clean_project_artifacts.py
