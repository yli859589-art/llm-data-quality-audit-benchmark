# 最终发布复核

## 原 P2-2 包

`dist/llm-data-quality-curation-p2-02.zip` 存在，实际 SHA-256：

`43E838E9C92AFAD1BE10B158741252F23AF16B1D1C7F8B792152A3EB376AE025`

与交付记录一致。该包为 source-only：不包含真实 C4/OpenWebText 分片或二进制模型
checkpoint，且 `RELEASE_MANIFEST.json` 明确声明这些限制。此前的 ZIP 测试、解压后
`scripts/quality_system.py --help` 均通过。

## 本次审计版

审计修复改变了源码与测试；因此会生成一个新的、不同文件名的 ZIP，原 P2-2 包不覆盖。
构建命令会生成 SHA-256、字节大小、ZIP CRC 和解压 CLI 验证的机器报告；最终交付摘要列出
该次构建的具体值。

按文件名审查未发现 `.env`、私钥或凭据；归档包含历史小型 JSONL 示例和元数据，未包含
声明的九个真实 C4/OpenWebText 分片或二进制模型 checkpoint。

## 运行边界

```powershell
pip install -e ".[data,tokenizers,ui]"
python scripts/quality_system.py --help
streamlit run apps/quality_system_app.py --server.address 127.0.0.1
```

安装与 CLI 是 `PASS` 的软件交付范围；真实语料训练仍为 `BLOCKED`。旧 LocalMax 发布
子系统的三项回归失败在本次新 ZIP 中保持公开限制，不能据此宣称“全仓零失败”。
