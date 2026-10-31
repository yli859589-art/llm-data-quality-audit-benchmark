# 最终缺陷登记

| ID | 级别 | 状态 | 证据与处置 |
| --- | --- | --- | --- |
| AUD-001 | P1 | FIXED | 根目录 pytest 递归收集 `test_tmp`，初次审计出现 288 collection errors；`pyproject.toml` 已限定 `tests`。 |
| AUD-002 | P1 | FIXED | Step 5/6/8 检查器默认覆盖受保护报告；已改为升级报告目录和 `--output`。 |
| AUD-003 | P1 | FIXED（如实标注） | 20 个历史清单哈希不匹配，所有相关文件仅在 `64b406a` 导入；未改证据，登记于 `src/artifacts_v2/legacy_integrity.py`。 |
| AUD-004 | P1 | FIXED | LocalMax/Level3 的原始字节哈希不跨 CRLF/LF checkout；保护检查改为 LF 规范化并增加回归测试。 |
| AUD-005 | P2 | FIXED | 测试把实际 MinHash/LSH 误断言为代理；现在明确断言 `proxy_used=false`。 |
| AUD-006 | P1 | OPEN | 旧 LocalMax 发布脚本会在其目录中重生成冻结元数据；全套隔离 pytest 的 3 个失败显示随生成顺序 registry 哈希会失配。未改写该历史发布物。 |
| AUD-007 | 外部阻碍 | BLOCKED | C4 3 个、OpenWebText 6 个真实分片缺失；禁止未经授权下载或伪造。 |

AUD-006 的最小复现：在隔离副本中运行 `python -m pytest -q`。结果为
`313 passed, 3 failed`；失败文件是 `test_localmax_release_registry_step10C.py`（2 项）和
`test_localmax_release_step10C.py`（1 项）。该问题限制的是旧 LocalMax 冻结发布包的
自洽性，不是 P2 统一服务的任务执行或数据筛选正确性。
