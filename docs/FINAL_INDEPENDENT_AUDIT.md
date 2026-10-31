# 最终独立审计

审计分支：`audit/final-independent-verification`。基线提交：`84ac8fd`；审计修复提交：
`7977be9`、`943fe56`、`fe97f5f`。

## 结论

| 范围 | 状态 | 结论 |
| --- | --- | --- |
| P0–P2 核心软件路径 | PASS_WITH_LIMITATIONS | 统一服务、筛选器、流式 Raw、任务恢复、导出与确定性 checkpoint 路径通过实际测试。 |
| 真实 C4/OpenWebText 训练实验 | BLOCKED | 9 个声明分片均缺失；没有下载、伪造或把夹具冒充正式语料。 |
| 完整历史 pytest | FAIL | 隔离执行为 `313 passed, 3 failed`；失败仅在旧 LocalMax 发布冻结子系统，详见缺陷登记。 |
| 旧实验完整性 | PASS_WITH_LIMITATIONS | 2,204 个受保护文件在主工作区与 P0 快照一致；20 个清单哈希缺陷保留为只读异常。 |

## 实际执行

```powershell
python -m pytest -q
# isolated Git worktree: 313 passed, 3 failed, 294.58s

python scripts/preflight_project.py --mode metadata `
  --baseline-manifest artifacts/upgrade_reports/p0-01_preflight/historical_baseline_sha256.json `
  --output test_tmp/audit_reports/preflight_after_canonical_fix.json
# 16 checks, 2,204 protected files unchanged

python scripts/check_training_manifests.py --include-step5 --output test_tmp/audit_reports/training.json
python scripts/check_urd_manifests.py --include-step6 --output test_tmp/audit_reports/urd.json
python scripts/check_mechanism_manifests.py --include-step8 --output test_tmp/audit_reports/mechanism.json
python scripts/check_evaluation_manifests.py --include-step7 --output test_tmp/audit_reports/evaluation.json
# 1 + 3 + 9 + 7 legacy exceptions; no undisclosed validation error
```

此前已加入并在本次全量套件中通过的确定性 CPU 测试，比较了中断恢复与连续训练的
模型权重；P1-2 测试覆盖 JSONL/GZ、原子分片、配置/输入变更阻断、跨分片去重与
SQLite 采样索引。MinHash 的持久索引仍使用 band 候选检索后再做精确 Jaccard 确认，
不执行全对全比较。

## 数据与界面

- C4：`0/3` 声明分片存在，历史元数据为 209,481 文档、100,002,807 token。
- OpenWebText：`0/6` 声明分片存在，历史元数据为 88,600 文档、100,004,093 token。
- 因此真实大语料训练、真实 PPL 与正式效果比较均为 `BLOCKED`。
- CLI/服务端端到端夹具路径由 `tests/test_p2_system_integration.py` 覆盖并通过。
  本次未重新完成六页 Streamlit 的人工点击流，故该 UI 人工验收为 `NOT_RUN`；不得由
  后端测试外推为完整 UI 手工验收。

## 已修复的审计问题

1. 根目录 pytest 会收集 `test_tmp` 的隔离副本并产生导入冲突；已在 `pyproject.toml`
   固定 `testpaths = ["tests"]`。
2. Step 5/6/8 清单检查器会默认改写受保护的 `artifacts/reports`；现默认写入
   `artifacts/upgrade_reports/manifest_checks/`，且支持显式 `--output`。
3. 训练、URD、机制和评估清单共 20 项导入前哈希不一致以前会被误写成通过；现在严格
   验证器仍失败，聚合检查器以 `passed_with_legacy_integrity_exceptions` 明确报告。
4. 旧保护哈希把 CRLF/LF 字节差异误当作数据篡改；保护检查现在仅对这四个文本结果使用
   LF 规范化哈希，其他工件哈希语义不变。
5. MinHash/LSH 是实际算法而非 PPL/质量代理；纠正了错误的测试标签，没有更改算法语义。

详见 [FINAL_DEFECT_REGISTER.md](FINAL_DEFECT_REGISTER.md) 与
[FINAL_RELEASE_VERIFICATION.md](FINAL_RELEASE_VERIFICATION.md)。
