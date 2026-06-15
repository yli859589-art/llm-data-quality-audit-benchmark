from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from _bootstrap import bootstrap, build_subprocess_env


ROOT = Path(__file__).resolve().parents[1]

bootstrap()


TAIL_LINES = 120
TAIL_CHARS = 8000
HEAVY_GROUPS = {
    "level3_execution_checks",
    "localmax_execution_checks",
    "localmax_v2_execution_checks",
    "localmax_v2_release_checks",
    "localmax_ccfc_artifact_checks",
}


@dataclass(frozen=True)
class CheckCommand:
    command: list[str]
    timeout_seconds: int | None = None


@dataclass(frozen=True)
class CheckGroup:
    name: str
    commands: list[CheckCommand]
    required: bool = True


@dataclass
class CommandResult:
    command: list[str]
    status: str
    returncode: int | None
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class GroupResult:
    name: str
    required: bool
    status: str
    command: list[str] = field(default_factory=list)
    returncode: int | None = None
    duration_seconds: float = 0.0
    stdout_tail: str = ""
    stderr_tail: str = ""
    commands: list[dict[str, object]] = field(default_factory=list)


STEP_TEST_FILES: dict[str, list[str]] = {
    "step2_data_tests": [
        "tests/test_data_sources_step2.py",
        "tests/test_dataset_manifest_step2.py",
        "tests/test_token_budget_step2.py",
        "tests/test_prepare_data_v2_step2.py",
        "tests/test_no_fallback_step2.py",
    ],
    "step3_tokenizer_tests": [
        "tests/test_tokenization_step3.py",
        "tests/test_tokenizer_manifest_step3.py",
        "tests/test_tokenizer_budget_step3.py",
        "tests/test_train_tokenizer_v2_step3.py",
    ],
    "step4_filter_tests": [
        "tests/test_filters_v2_step4.py",
        "tests/test_filter_manifests_step4.py",
        "tests/test_run_filter_v2_step4.py",
        "tests/test_keep_rate_step4.py",
        "tests/test_proxy_filter_boundaries_step4.py",
    ],
    "step5_training_tests": [
        "tests/test_models_v2_step5.py",
        "tests/test_training_config_step5.py",
        "tests/test_training_data_adapter_step5.py",
        "tests/test_train_model_v2_step5.py",
        "tests/test_training_manifests_step5.py",
        "tests/test_training_no_main_results_pollution_step5.py",
    ],
    "step6_urd_tests": [
        "tests/test_urd_components_step6.py",
        "tests/test_urd_selector_step6.py",
        "tests/test_urd_pareto_step6.py",
        "tests/test_urd_ablation_step6.py",
        "tests/test_urd_manifest_step6.py",
        "tests/test_urd_no_main_results_pollution_step6.py",
    ],
    "step7_evaluation_tests": [
        "tests/test_evaluation_schema_step7.py",
        "tests/test_lm_metrics_step7.py",
        "tests/test_downstream_protocol_step7.py",
        "tests/test_risk_eval_step7.py",
        "tests/test_diversity_eval_step7.py",
        "tests/test_cost_eval_step7.py",
        "tests/test_stability_step7.py",
        "tests/test_pareto_eval_step7.py",
        "tests/test_evaluation_manifests_step7.py",
        "tests/test_evaluation_no_main_results_pollution_step7.py",
    ],
    "step8_mechanism_tests": [
        "tests/test_mechanism_schema_step8.py",
        "tests/test_proxy_utility_step8.py",
        "tests/test_overfiltering_step8.py",
        "tests/test_diversity_loss_step8.py",
        "tests/test_domain_shift_step8.py",
        "tests/test_rank_stability_step8.py",
        "tests/test_tokenizer_sensitivity_step8.py",
        "tests/test_scale_trend_step8.py",
        "tests/test_failure_taxonomy_step8.py",
        "tests/test_pareto_mechanism_step8.py",
        "tests/test_mechanism_manifests_step8.py",
        "tests/test_mechanism_no_main_results_pollution_step8.py",
    ],
    "step9_readiness_tests": [
        "tests/test_readiness_v2_step9.py",
        "tests/test_level3_gates_step9.py",
        "tests/test_artifact_registry_v2_step9.py",
        "tests/test_claim_map_step9.py",
        "tests/test_no_smoke_in_main_step9.py",
        "tests/test_no_protocol_as_completed_step9.py",
        "tests/test_no_level2_as_level3_step9.py",
        "tests/test_run_all_checks_step9.py",
        "tests/test_registry_to_tables_step9.py",
        "tests/test_step9_technical_debt_fixes.py",
        "tests/test_step9_level3_artifact_hygiene.py",
    ],
    "step10A_protocol_tests": [
        "tests/test_level3_protocol_step10A.py",
        "tests/test_level3_preflight_step10A.py",
        "tests/test_level3_artifact_paths_step10A.py",
        "tests/test_level3_claim_boundary_step10A.py",
        "tests/test_level3_dryrun_scripts_step10A.py",
        "tests/test_step10A_no_execution_pollution.py",
        "tests/test_artifact_scanner_path_independence_step10A.py",
        "tests/test_artifact_registry_finalization_step10A.py",
        "tests/test_step10A_hotfix_no_execution_pollution.py",
    ],
    "step10B_execution_tests": [
        "tests/test_step10B_environment.py",
        "tests/test_step10B_data_execution.py",
        "tests/test_step10B_tokenizer_execution.py",
        "tests/test_step10B_filter_execution.py",
        "tests/test_step10B_training_execution.py",
        "tests/test_step10B_evaluation_execution.py",
        "tests/test_step10B_mechanism_execution.py",
        "tests/test_step10B_registry_tables.py",
        "tests/test_step10B_readiness.py",
        "tests/test_step10B_no_false_level3_claims.py",
    ],
    "step10B_localmax_tests": [
        "tests/test_localmax_execution_fix_step10B.py",
        "tests/test_localmax_minimal_data_threshold_step10B.py",
        "tests/test_localmax_minimal_training_outputs_step10B.py",
        "tests/test_localmax_nonempty_tables_step10B.py",
        "tests/test_localmax_no_fake_completion_step10B.py",
        "tests/test_localmax_training_strengthen_step10B.py",
        "tests/test_localmax_ppl_clipping_step10B.py",
        "tests/test_localmax_strengthened_tables_step10B.py",
        "tests/test_localmax_strengthened_readiness_step10B.py",
        "tests/test_localmax_strengthened_no_false_claims_step10B.py",
        "tests/test_localmax_environment_step10B.py",
        "tests/test_localmax_data_step10B.py",
        "tests/test_localmax_tokenizer_step10B.py",
        "tests/test_localmax_filters_step10B.py",
        "tests/test_localmax_training_step10B.py",
        "tests/test_localmax_evaluation_step10B.py",
        "tests/test_localmax_mechanism_step10B.py",
        "tests/test_localmax_registry_tables_step10B.py",
        "tests/test_localmax_readiness_step10B.py",
        "tests/test_localmax_no_false_level3_claims_step10B.py",
    ],
    "step10C_localmax_release_tests": [
        "tests/test_localmax_release_step10C.py",
        "tests/test_localmax_claim_boundary_step10C.py",
        "tests/test_localmax_release_registry_step10C.py",
        "tests/test_localmax_readme_resume_step10C.py",
        "tests/test_localmax_no_false_level3_claims_step10C.py",
        "tests/test_localmax_release_figures_step10C.py",
        "tests/test_localmax_release_figure_readability_step10C_hotfix.py",
        "tests/test_localmax_release_cross_platform_hashes_step10C_hotfix.py",
        "tests/test_localmax_release_idempotency_step10C_hotfix.py",
        "tests/test_localmax_release_canonical_io_step10C_hotfix.py",
        "tests/test_localmax_release_bundle_scope_step10C_hotfix.py",
        "tests/test_localmax_release_bundle_links_step10C_hotfix.py",
        "tests/test_localmax_release_no_result_modification_step10C_hotfix.py",
    ],
    "localmax_v2_tests": [
        "tests/test_localmax_v2_metric_audit.py",
        "tests/test_localmax_v2_data_scale.py",
        "tests/test_localmax_v2_filter_execution.py",
        "tests/test_localmax_v2_training_budget.py",
        "tests/test_localmax_v2_evaluation.py",
        "tests/test_localmax_v2_statistics.py",
        "tests/test_localmax_v2_mechanism.py",
        "tests/test_localmax_v2_tables.py",
        "tests/test_localmax_v2_readiness.py",
        "tests/test_localmax_v2_claim_boundary.py",
        "tests/test_localmax_v2_registry_truthfulness.py",
        "tests/test_localmax_v2_bundle_integrity.py",
        "tests/test_localmax_v2_no_historical_pollution.py",
    ],
    "localmax_ccfc_tests": [
        "tests/test_localmax_ccfc_strengthening.py",
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _existing(files: list[str]) -> list[str]:
    return [path for path in files if (ROOT / path).exists()]


def _pytest_command(files: list[str]) -> list[str]:
    existing = _existing(files)
    return [sys.executable, "-m", "pytest", *existing, "-q"]


def _legacy_test_files() -> list[str]:
    assigned = {path for files in STEP_TEST_FILES.values() for path in files}
    return [
        path.relative_to(ROOT).as_posix()
        for path in sorted((ROOT / "tests").glob("test_*.py"))
        if path.relative_to(ROOT).as_posix() not in assigned
    ]


def _report_command(command: list[str]) -> list[str]:
    display = [str(part) for part in command]
    if display and Path(display[0]).resolve() == Path(sys.executable).resolve():
        display[0] = "python"
    return display


def _command_text(command: list[str]) -> str:
    report = _report_command(command)
    if os.name == "nt":
        return subprocess.list2cmdline(report)
    return shlex.join(report)


def _tail(lines: deque[str]) -> str:
    text = "".join(lines)
    if len(text) > TAIL_CHARS:
        return text[-TAIL_CHARS:]
    return text


def _reader_thread(stream, sink: deque[str], prefix: str = "") -> None:
    try:
        for line in iter(stream.readline, ""):
            sink.append(line)
            print(f"{prefix}{line}", end="", flush=True)
    finally:
        stream.close()


def _terminate(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except FileNotFoundError:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_child_command(command: list[str], timeout: int) -> CommandResult:
    display = _report_command(command)
    print(f"RUN {_command_text(command)}", flush=True)
    started = time.perf_counter()
    stdout_lines: deque[str] = deque(maxlen=TAIL_LINES)
    stderr_lines: deque[str] = deque(maxlen=TAIL_LINES)
    popen_kwargs: dict[str, object] = {
        "cwd": ROOT,
        "env": build_subprocess_env(),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "bufsize": 1,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    process = subprocess.Popen([str(part) for part in command], **popen_kwargs)
    assert process.stdout is not None
    assert process.stderr is not None
    stdout_thread = threading.Thread(target=_reader_thread, args=(process.stdout, stdout_lines), daemon=True)
    stderr_thread = threading.Thread(target=_reader_thread, args=(process.stderr, stderr_lines, "ERR "), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    status = "passed"
    returncode: int | None
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        status = "timeout"
        returncode = 124
        _terminate(process)
    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    duration = time.perf_counter() - started
    if status != "timeout" and returncode != 0:
        status = "failed"
    if status == "passed":
        print(f"OK {_command_text(command)}", flush=True)
    else:
        print(f"FAILED {_command_text(command)}", flush=True)
        if status == "timeout":
            print(f"timeout={timeout}s", flush=True)
        else:
            print(f"returncode={returncode}", flush=True)
    return CommandResult(
        command=display,
        status=status,
        returncode=returncode,
        duration_seconds=duration,
        stdout_tail=_tail(stdout_lines),
        stderr_tail=_tail(stderr_lines),
    )


def _check_groups(skip_tests: bool) -> dict[str, CheckGroup]:
    groups: list[CheckGroup] = []
    if not skip_tests:
        groups.append(CheckGroup("legacy_core_tests", [CheckCommand(_pytest_command(_legacy_test_files()))]))
        for name in [
            "step2_data_tests",
            "step3_tokenizer_tests",
            "step4_filter_tests",
            "step5_training_tests",
            "step6_urd_tests",
            "step7_evaluation_tests",
            "step8_mechanism_tests",
            "step9_readiness_tests",
            "step10A_protocol_tests",
            "step10B_execution_tests",
            "step10B_localmax_tests",
            "step10C_localmax_release_tests",
            "localmax_v2_tests",
            "localmax_ccfc_tests",
        ]:
            groups.append(CheckGroup(name, [CheckCommand(_pytest_command(STEP_TEST_FILES[name]))]))
    groups.extend(
        [
            CheckGroup(
                "manifest_checks",
                [
                    CheckCommand([sys.executable, "scripts/check_filter_manifests.py", "--include-step4"]),
                    CheckCommand([sys.executable, "scripts/check_training_manifests.py", "--include-step5"]),
                    CheckCommand([sys.executable, "scripts/check_urd_manifests.py", "--include-step6"]),
                    CheckCommand([sys.executable, "scripts/check_evaluation_manifests.py", "--include-step7"]),
                    CheckCommand([sys.executable, "scripts/check_mechanism_manifests.py", "--include-step8"]),
                ],
            ),
            CheckGroup(
                "artifact_checks",
                [
                    CheckCommand([sys.executable, "scripts/check_repo.py", "--clean"]),
                    CheckCommand([sys.executable, "scripts/capture_environment.py"]),
                    CheckCommand([sys.executable, "scripts/check_registry_schema.py"]),
                    CheckCommand([sys.executable, "scripts/check_artifact_lineage.py"]),
                    CheckCommand([sys.executable, "scripts/check_main_results_purity.py"]),
                ],
            ),
            CheckGroup(
                "claim_checks",
                [
                    CheckCommand([sys.executable, "scripts/check_claims_supported.py"]),
                    CheckCommand([sys.executable, "scripts/check_claim_hygiene.py"]),
                    CheckCommand([sys.executable, "scripts/check_claim_map.py"]),
                    CheckCommand([sys.executable, "scripts/check_no_forbidden_claims.py"]),
                    CheckCommand([sys.executable, "scripts/check_no_smoke_in_main.py"]),
                    CheckCommand([sys.executable, "scripts/check_no_protocol_as_completed.py"]),
                    CheckCommand([sys.executable, "scripts/check_no_level2_as_level3.py"]),
                ],
            ),
            CheckGroup(
                "level3_gate_checks",
                [
                    CheckCommand([sys.executable, "scripts/check_level3_gates.py"]),
                    CheckCommand([sys.executable, "scripts/check_level3_protocol.py"]),
                    CheckCommand([sys.executable, "scripts/check_level3_preflight.py"]),
                    CheckCommand([sys.executable, "scripts/write_step10A_readiness_report.py"]),
                ],
            ),
            CheckGroup(
                "dataaudit_lm_checks",
                [
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/audit_metric_correctness.py"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/audit_experiment_fairness.py"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/verify_artifacts.py"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/write_migration_and_protocol_reports.py"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/run_rehearsal.py"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/finalize_release.py", "--audit-only"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/verify_document_consistency.py"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/verify_fresh_clone.py", "--light"]),
                    CheckCommand([sys.executable, "scripts/dataaudit_lm/generate_naming_inventory.py"]),
                ],
            ),
            CheckGroup(
                "level3_execution_checks",
                [
                    CheckCommand([sys.executable, "scripts/level3/check_heavy_environment.py"]),
                    CheckCommand([sys.executable, "scripts/level3/run_rehearsal.py", "--config", "configs/level3/rehearsal_50m.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/prepare_level3_data.py", "--config", "configs/level3/data_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/prepare_level3_tokenizers.py", "--config", "configs/level3/tokenizers.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/run_level3_filters.py", "--config", "configs/level3/filter_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/run_level3_training.py", "--config", "configs/level3/training_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/run_level3_evaluation.py", "--config", "configs/level3/evaluation_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/run_level3_analysis.py", "--config", "configs/level3/mechanism_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/level3/finalize_level3_execution.py"]),
                ],
            ),
            CheckGroup(
                "localmax_execution_checks",
                [
                    CheckCommand([sys.executable, "scripts/localmax/check_localmax_environment.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/prepare_localmax_tokenizer.py", "--config", "configs/localmax/tokenizer.yaml"]),
                    CheckCommand([sys.executable, "scripts/localmax/prepare_localmax_data_minimal.py", "--config", "configs/localmax/data_matrix_minimal.yaml"], timeout_seconds=900),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_filters_minimal.py", "--config", "configs/localmax/filter_matrix_minimal.yaml"]),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_training_minimal.py", "--config", "configs/localmax/training_matrix_minimal.yaml"], timeout_seconds=900),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_evaluation_minimal.py", "--config", "configs/localmax/evaluation_matrix_minimal.yaml"]),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_analysis_minimal.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_training_strengthened.py", "--config", "configs/localmax/training_strengthened.yaml"], timeout_seconds=1200),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_evaluation_strengthened.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/run_localmax_analysis_strengthened.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/finalize_localmax_execution.py"]),
                ],
            ),
            CheckGroup(
                "localmax_release_checks",
                [
                    CheckCommand([sys.executable, "scripts/localmax/make_localmax_release_tables.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/make_localmax_release_figures.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/check_localmax_release_claims.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/check_localmax_release_bundle.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/check_localmax_release_idempotency.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/finalize_localmax_release.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/check_localmax_release_claims.py"]),
                    CheckCommand([sys.executable, "scripts/localmax/check_localmax_release_bundle.py"]),
                ],
            ),
            CheckGroup(
                "localmax_v2_execution_checks",
                [
                    CheckCommand([sys.executable, "scripts/localmax_v2/check_localmax_v2_environment.py"]),
                    CheckCommand([sys.executable, "scripts/localmax_v2/audit_lm_metric_correctness.py"]),
                    CheckCommand([sys.executable, "scripts/localmax_v2/prepare_localmax_v2_data.py", "--config", "configs/localmax_v2/data_matrix.yaml"], timeout_seconds=1800),
                    CheckCommand([sys.executable, "scripts/localmax_v2/run_localmax_v2_filters.py", "--config", "configs/localmax_v2/filter_matrix.yaml"], timeout_seconds=1200),
                    CheckCommand([sys.executable, "scripts/localmax_v2/benchmark_training_throughput.py"], timeout_seconds=600),
                    CheckCommand([sys.executable, "scripts/localmax_v2/run_localmax_v2_training.py", "--config", "configs/localmax_v2/training_matrix.yaml"], timeout_seconds=3600),
                    CheckCommand([sys.executable, "scripts/localmax_v2/run_localmax_v2_evaluation.py", "--config", "configs/localmax_v2/evaluation_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/localmax_v2/run_localmax_v2_downstream.py", "--config", "configs/localmax_v2/downstream_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/localmax_v2/run_localmax_v2_analysis.py", "--config", "configs/localmax_v2/mechanism_matrix.yaml"]),
                    CheckCommand([sys.executable, "scripts/localmax_v2/finalize_localmax_v2_execution.py"]),
                ],
            ),
            CheckGroup(
                "localmax_v2_release_checks",
                [
                    CheckCommand([sys.executable, "scripts/localmax_v2/finalize_localmax_v2_release.py"]),
                ],
            ),
            CheckGroup(
                "localmax_ccfc_artifact_checks",
                [
                    CheckCommand([sys.executable, "scripts/localmax_ccfc/check_ccfc_artifacts.py"]),
                    CheckCommand([sys.executable, "scripts/localmax_ccfc/finalize_ccfc_project.py"]),
                ],
            ),
            CheckGroup(
                "registry_finalization_checks",
                [
                    CheckCommand([sys.executable, "scripts/finalize_artifact_registry_v2.py"]),
                    CheckCommand([sys.executable, "scripts/check_registry_to_tables.py"]),
                    CheckCommand([sys.executable, "scripts/check_main_results_from_registry.py"]),
                ],
            ),
        ]
    )
    return {group.name: group for group in groups}


def _run_group(group: CheckGroup, timeout: int) -> GroupResult:
    started = time.perf_counter()
    command_results: list[CommandResult] = []
    for check in group.commands:
        command_timeout = check.timeout_seconds or timeout
        result = run_child_command(check.command, command_timeout)
        command_results.append(result)
        if result.status != "passed":
            break
    if not command_results:
        return GroupResult(
            name=group.name,
            required=group.required,
            status="skipped",
            duration_seconds=time.perf_counter() - started,
        )
    status = "passed"
    if any(result.status == "timeout" for result in command_results):
        status = "timeout"
    elif any(result.status == "failed" for result in command_results):
        status = "failed"
    stdout_tail = "".join(result.stdout_tail for result in command_results)[-TAIL_CHARS:]
    stderr_tail = "".join(result.stderr_tail for result in command_results)[-TAIL_CHARS:]
    returncode = next((result.returncode for result in command_results if result.status != "passed"), 0)
    return GroupResult(
        name=group.name,
        required=group.required,
        status=status,
        command=command_results[-1].command,
        returncode=returncode,
        duration_seconds=time.perf_counter() - started,
        stdout_tail=stdout_tail,
        stderr_tail=stderr_tail,
        commands=[asdict(result) for result in command_results],
    )


def _overall_status(results: list[GroupResult]) -> str:
    required = [result for result in results if result.required]
    if any(result.status == "timeout" for result in required):
        return "timeout"
    if any(result.status == "failed" for result in required):
        return "failed"
    if any(result.status == "skipped" for result in required):
        return "completed_with_failures"
    return "passed"


def _write_reports(
    *,
    results: list[GroupResult],
    skipped_groups: list[str],
    started_at: str,
    started_perf: float,
    json_out: Path,
    md_out: Path,
) -> dict[str, object]:
    finished_at = _now()
    status = _overall_status(results)
    payload = {
        "status": status,
        "overall_passed": status == "passed",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": time.perf_counter() - started_perf,
        "groups": [asdict(result) for result in results],
        "failed_groups": [result.name for result in results if result.required and result.status == "failed"],
        "timeout_groups": [result.name for result in results if result.required and result.status == "timeout"],
        "skipped_groups": skipped_groups + [result.name for result in results if result.status == "skipped"],
    }
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Run All Checks Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Overall passed: `{payload['overall_passed']}`",
        f"- Started at: `{started_at}`",
        f"- Finished at: `{finished_at}`",
        f"- Duration seconds: `{payload['duration_seconds']:.3f}`",
        f"- Failed groups: `{', '.join(payload['failed_groups']) if payload['failed_groups'] else 'none'}`",
        f"- Timeout groups: `{', '.join(payload['timeout_groups']) if payload['timeout_groups'] else 'none'}`",
        f"- Skipped groups: `{', '.join(payload['skipped_groups']) if payload['skipped_groups'] else 'none'}`",
        "",
        "| Group | Required | Status | Return Code | Duration Seconds |",
        "|---|---:|---|---:|---:|",
    ]
    for result in results:
        returncode = "" if result.returncode is None else str(result.returncode)
        lines.append(
            f"| `{result.name}` | `{result.required}` | `{result.status}` | "
            f"{returncode} | {result.duration_seconds:.3f} |"
        )
    lines.extend(["", "## Command Tails", ""])
    for result in results:
        lines.append(f"### {result.name}")
        lines.append("")
        lines.append(f"- Command: `{' ; '.join(_command_text(command['command']) for command in result.commands) if result.commands else 'none'}`")
        lines.append(f"- Status: `{result.status}`")
        lines.append("")
        if result.stdout_tail:
            lines.append("```text")
            lines.append(result.stdout_tail.strip())
            lines.append("```")
        if result.stderr_tail:
            lines.append("```text")
            lines.append(result.stderr_tail.strip())
            lines.append("```")
        if not result.stdout_tail and not result.stderr_tail:
            lines.append("_No captured output._")
        lines.append("")
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run grouped repository checks with truthful timeout/failure reports.")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds for each group command.")
    parser.add_argument("--overall-timeout", type=int, default=0, help="Reserved for compatibility; groups still report individually.")
    parser.add_argument("--group", action="append", default=[], help="Run one or more named groups.")
    parser.add_argument("--include-heavy", action="store_true", help="Include heavy execution groups that may rerun training/data preparation.")
    parser.add_argument("--list-groups", action="store_true")
    parser.add_argument("--json-out", default="artifacts/reports/run_all_checks_report.json")
    parser.add_argument("--md-out", default="artifacts/reports/run_all_checks_report.md")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    groups = _check_groups(skip_tests=args.skip_tests)
    if args.list_groups:
        for name in groups:
            print(name)
        return
    if args.group:
        selected_names = args.group
    elif args.include_heavy:
        selected_names = list(groups)
    else:
        selected_names = [name for name in groups if name not in HEAVY_GROUPS]
    unknown = [name for name in selected_names if name not in groups]
    if unknown:
        raise SystemExit("Unknown check group(s): " + ", ".join(unknown))
    skipped = [name for name in groups if name not in selected_names]
    started_at = _now()
    started_perf = time.perf_counter()
    results: list[GroupResult] = []
    for name in selected_names:
        result = _run_group(groups[name], timeout=args.timeout)
        results.append(result)
        if result.required and result.status != "passed":
            break
    payload = _write_reports(
        results=results,
        skipped_groups=skipped,
        started_at=started_at,
        started_perf=started_perf,
        json_out=ROOT / args.json_out if not Path(args.json_out).is_absolute() else Path(args.json_out),
        md_out=ROOT / args.md_out if not Path(args.md_out).is_absolute() else Path(args.md_out),
    )
    if payload["status"] != "passed":
        raise SystemExit(f"Checks did not pass. status={payload['status']} failed_groups={payload['failed_groups']} timeout_groups={payload['timeout_groups']}")
    print("All checks passed.")


if __name__ == "__main__":
    main()
