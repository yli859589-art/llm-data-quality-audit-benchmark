#!/usr/bin/env bash
set -euo pipefail

python scripts/check_level3_protocol.py
python scripts/check_level3_preflight.py
python scripts/level3/prepare_level3_data_plan.py
python scripts/level3/run_level3_filters_plan.py
python scripts/level3/run_level3_training_plan.py
python scripts/level3/run_level3_evaluation_plan.py
python scripts/level3/run_level3_analysis_plan.py
python scripts/level3/release_level3_plan.py

