# SEC RAG 摄取 PoC

补充状态（2026-10-05）：`network_executed=true`、`status=completed`、corpus aggregate SHA-256=`45172c...`；本轮完成正文下载、HTML 清洗、解析、section、chunks 与 citation，未实现 Embedding/BM25/RRF/Reranker/LLM/Agent。

## 2026-10-05 真实小批量结果

已完成 10/10 个真实 filing bundle（5 K、5 Q）：19,573,518 raw bytes、399 sections、2,003 chunks；request 12、retry 2、failed 0、model_calls 0。100 份仍为候选，剩余 90 份未下载；本轮不是完整 RAG。下一步确认离线检索/评测方案。

截至 2026-09-26，本阶段完成离线 SEC 文档解析、章节识别、确定性分块、SHA-256 溯源和安全契约校验。`build_sec_chunks.py` 只读取 `.local_data` 下显式指定的文件，输出 document/chunks/manifest，并以临时目录批量原子替换；不会联网、调用模型或写入向量库。

正文下载器已完成最多 10 份最新 10-K/10-Q 的真实验收；100 份仍为候选，完成检索验收前不称为完整 RAG。

## 输入与约束

- metadata 必须包含规范化 symbol、非零十位 CIK、合法 accession、允许表单（10-K/10-Q/8-K 及修订）、HTTPS SEC 来源 URL。
- filing 的 accepted/published 时间使用 UTC 比较；SEC 14 位时间按 `America/New_York` 解释后转换 UTC。
- 原始内容按 bytes 计算 SHA-256；调用者提供哈希时必须重新计算并匹配。
- `target_chars > overlap_chars >= 0`，空文档拒绝。
- 输入和输出只允许在 `.local_data` 内，拒绝符号链接、目录和超大文件。

## 当前边界

这是离线解析 PoC，不是 RAG 系统。没有 embedding、BM25、RRF、reranker、LLM、Agent、数据库或前端连接。真实多公司下载仍需显式 `--network`、有效 `FINSIGHT_SEC_USER_AGENT`、限额与下载前审查。

## 运行

```bash
PYTHONPATH=src python3 scripts/build_sec_chunks.py \
  --input .local_data/sec/raw/<filing> \
  --metadata .local_data/sec/normalized/<metadata>.json \
  --symbol NVDA --as-of 2026-09-18 \
  --output-dir .local_data/sec/rag
```

多公司候选清单只使用本地 ticker mapping 和 submissions：

```bash
PYTHONPATH=src python3 scripts/build_sec_corpus.py \
  --ticker-mapping .local_data/sec/normalized/<mapping>.json \
  --submissions-dir .local_data/sec/normalized \
  --output /tmp/sec-candidates.json
```

五家公司 submissions 与 100 份候选清单已完成验证；本轮正文下载仅完成 10 份，不能将候选数量描述为完整 corpus。
