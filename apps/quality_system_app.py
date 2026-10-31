"""Streamlit UI; all operations delegate to quality_system.service."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover - displayed by the launch command
    raise SystemExit("缺少 Web 可选依赖。请执行: pip install -e '.[ui]'") from exc

from quality_system.service import QualitySystemService  # noqa: E402

service = QualitySystemService(ROOT)
st.set_page_config(page_title="LLM 数据质量系统", page_icon="📊", layout="wide")
st.title("LLM Training Data Quality & Curation System")
st.caption("本地运行 · 真实后端任务 · P2-1 统一入口")
page = st.sidebar.radio(
    "功能", ["项目总览", "数据集管理", "数据质量分析", "筛选策略", "任务监控", "结果与导出"]
)

if page == "项目总览":
    data = service.overview()
    st.warning(data["real_corpus_notice"])
    st.metric("已完成任务", data["completed_tasks"])
    st.write(f"设备：`{data['device']}`")
    st.subheader("历史正式语料状态")
    st.dataframe(data["historical_datasets"], use_container_width=True)
    st.subheader("已导入数据集")
    st.dataframe(data["datasets"], use_container_width=True)
    st.subheader("最近任务")
    st.dataframe(data["tasks"], use_container_width=True)
elif page == "数据集管理":
    st.subheader("导入本地数据集")
    with st.form("import"):
        dataset_id = st.text_input("数据集 ID", "my_dataset")
        path = st.text_input("本地文件路径（JSONL / JSONL.GZ / Parquet）")
        source = st.text_input("来源", "local")
        version = st.text_input("版本", "")
        submitted = st.form_submit_button("扫描并登记")
    if submitted:
        try:
            st.json(service.import_dataset(dataset_id, path, source=source, version=version))
        except Exception as exc:
            st.error(f"导入失败：{type(exc).__name__}: {exc}")
    st.dataframe(service.datasets(), use_container_width=True)
elif page == "数据质量分析":
    names = [row["dataset_id"] for row in service.datasets()]
    if not names:
        st.info("请先在“数据集管理”导入数据。")
        st.stop()
    dataset_id = st.selectbox("数据集", names)
    limit = st.number_input("最大分析样本数", min_value=1, value=10000)
    if st.button("开始实际分析"):
        try:
            report = service.analyze(dataset_id, sample_limit=int(limit))
            st.caption(f"范围：{report['analysis_scope']}，样本 {report['sample_documents']} 条")
            st.json(report)
        except Exception as exc:
            st.error(f"分析失败：{type(exc).__name__}: {exc}")
elif page == "筛选策略":
    names = [row["dataset_id"] for row in service.datasets()]
    if not names:
        st.info("请先导入数据。")
        st.stop()
    strategy = st.selectbox(
        "策略",
        list(service.strategies()),
        format_func=lambda key: service.strategies()[key]["label"],
    )
    st.info(service.strategies()[strategy]["description"])
    dataset_id = st.selectbox("数据集", names)
    keep = st.number_input("目标保留率（可选）", min_value=0.01, max_value=1.0, value=1.0)
    max_docs = st.number_input("非流式策略最大文档数", min_value=1, value=100000)
    device = st.selectbox(
        "运行设备请求",
        ["auto", "cpu", "cuda"],
        help="当前筛选器主要在 CPU 执行；该选择会被记录，未使用的设备能力不会伪报。",
    )
    params = st.text_area("算法参数 JSON", "{}")
    config_name = st.text_input("配置名称（用于保存/加载）", "")
    if st.button("保存当前配置"):
        try:
            st.success(
                str(
                    service.save_config(
                        config_name,
                        {
                            "dataset_id": dataset_id,
                            "strategy": strategy,
                            "target_keep_rate": float(keep),
                            "max_documents": int(max_docs),
                            "params": json.loads(params),
                            "device_request": device,
                            "allow_proxy": True,
                        },
                    )
                )
            )
        except Exception as exc:
            st.error(f"保存失败：{type(exc).__name__}: {exc}")
    if st.button("加载已保存配置"):
        try:
            st.json(service.load_config(config_name))
        except Exception as exc:
            st.error(f"加载失败：{type(exc).__name__}: {exc}")
    if st.button("配置预检并启动任务"):
        try:
            config = {
                "dataset_id": dataset_id,
                "strategy": strategy,
                "target_keep_rate": float(keep),
                "max_documents": int(max_docs),
                "params": json.loads(params),
                "device_request": device,
                "allow_proxy": True,
            }
            st.json(service.validate_filter_config(config))
            task = service.start_task(config)
            st.success(f"已启动：{task['task_id']}")
            st.json(task)
        except Exception as exc:
            st.error(f"启动失败：{type(exc).__name__}: {exc}")
elif page == "任务监控":
    st.caption("状态保存在 artifacts/p2_01_system/tasks.sqlite；刷新页面后仍可查看。")
    for task in service.task_list():
        with st.expander(f"{task['task_id']} · {task['status']}"):
            st.json(task)
            st.code(service.task_log(task["task_id"]), language="text")
            if "peak_tracemalloc_bytes" not in task.get("result", {}):
                st.caption("内存/吞吐指标：未提供（该后端未产生该指标）。")
            left, right = st.columns(2)
            if left.button("恢复/重试", key=f"resume-{task['task_id']}"):
                st.json(service.execute_task(task["task_id"]))
            if right.button("取消", key=f"cancel-{task['task_id']}"):
                st.json(service.cancel_task(task["task_id"]))
elif page == "结果与导出":
    completed = [task for task in service.task_list() if task.get("status") == "completed"]
    if not completed:
        st.info("尚无已完成任务；模型评估：未运行。")
        st.stop()
    task_id = st.selectbox("已完成任务", [task["task_id"] for task in completed])
    task = service.task(task_id)
    st.json(task.get("result", {}))
    training_manifest = st.text_input(
        "可选：Step 5 训练清单路径，用于实际调用既有 LM smoke evaluator", ""
    )
    if training_manifest and st.button("运行 LM smoke 评估"):
        try:
            st.json(service.evaluate_smoke_training(training_manifest))
        except Exception as exc:
            st.error(f"评估失败：{type(exc).__name__}: {exc}")
    if not training_manifest:
        st.caption("模型评估：未运行（不会把历史版本指标冒充为本次运行结果）。")
    if st.button("导出实际输出 ZIP"):
        try:
            st.success(str(service.export_task(task_id)))
        except Exception as exc:
            st.error(f"导出失败：{type(exc).__name__}: {exc}")
