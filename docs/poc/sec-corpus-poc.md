# 多公司 SEC 语料 PoC

状态（2026-09-26）：候选清单已完成，五家公司共确认 100 份候选（每家最多 5 份 10-K、15 份 10-Q）。上一阶段 submissions metadata refresh 共 4 次 SEC 请求；本阶段正文下载请求为 0。100 份是候选，不是已下载语料；完成下一轮验收前不能称为完整 RAG。

## 离线小批量计划

下载器只接受经验证的 candidate manifest。`--dry-run` 不联网、不创建正文产物，只验证身份、截止时间、SEC Archives URL、重复 accession 和预算：

```bash
PYTHONPATH=src python3 scripts/build_sec_corpus.py \
  --candidate-manifest .local_data/rag/corpus/semiconductor-candidates-2026-09-18.json \
  --output-dir .local_data/rag/corpus \
  --dry-run --latest-per-form-per-company \
  --max-documents 10 --max-documents-per-company 2
```

稳定排序使用 ticker、form、accepted_at/filing_date、accession number；当前计划最多 5 家各一份最新 10-K 与一份最新 10-Q，共 10 份。下载前预检最多 10 个文档对象、每件 50 MiB、总计 500 MiB；HTTP 最大尝试数为文档数 ×（`SECConfig.max_retries + 1`），默认 10 × 3 = 30。

## 单份 filing 的完整批次

每份 filing 必须同时产生 raw、metadata、document、chunks 和 ingestion manifest 五类产物，固定放在单一 bundle 目录 `TICKER/filings/<accession-stem>/`。所有下载、SHA-256 校验、metadata 构建、HTML 解析、章节提取、chunk 生成及 JSON/JSONL 重新解析验证先写入 `filings` 同级的 `.batch-*` 临时 bundle，最后只用一次目录级原子 rename 提交。任何失败都会清理临时 bundle 并回滚本批次；已完成的其他 filing 不受影响。禁止通过符号链接写出 `.local_data`。

默认不覆盖已有 accession：五类产物完整、身份一致且 SHA-256 一致时标记 `already_completed` 并跳过；不完整、哈希不一致或身份冲突安全失败。显式 `--overwrite` 才允许原子替换：旧 bundle 先 rename 为隐藏 `.backup-*`，新 bundle 再 rename 到 final；启动或每份文档处理前，backup 存在且 final 缺失则恢复，二者都存在则 final 视为已提交并清理 backup。替换中途失败会恢复旧五件套。

统计字段包括 `planned_document_count`、`attempted_document_count`、`completed_document_count`、`already_completed_count`、`overwritten_document_count`、`failed_document_count`、`request_count`、`retry_count`、`downloaded_bytes`、`network_executed`、`model_calls`、`status`。单文档失败会停止本批次，状态为 `failed`（无成功）或 `partial`（已有成功），不会伪称完整成功。

## 边界

正文下载仍必须显式传入 `--network` 并配置 `FINSIGHT_SEC_USER_AGENT`；缺失 User-Agent、manifest 无效、预算非法、输出路径不安全或身份冲突均在首个网络请求前停止。本轮不执行 ingestion、Embedding、向量数据库或 LLM。下一轮只执行上述最多 10 份小批量真实正文下载，独立验收通过后再决定后续范围。
