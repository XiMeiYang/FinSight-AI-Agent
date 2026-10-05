# 多公司 SEC 语料 PoC

## 2026-10-05 真实小批量结果

已完成 10/10 个完整 bundle（5 份 10-K、5 份 10-Q，每家公司 2 份）。本轮执行正文下载、HTML 清洗、文档解析、section 识别、chunks 与 citation 字段保存；不是完整 RAG。

| 公司 | K/Q | raw bytes | sections | chunks | earliest / latest filing | fail |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| AMD | 1/1 | 3,523,416 | 64 | 416 | 2026-02-04 / 2026-08-05 | 0 |
| AVGO | 1/1 | 4,430,060 | 68 | 377 | 2025-12-18 / 2026-09-10 | 0 |
| INTC | 1/1 | 5,037,625 | 134 | 470 | 2026-01-23 / 2026-07-24 | 0 |
| NVDA | 1/1 | 3,485,085 | 66 | 332 | 2026-02-25 / 2026-08-26 | 0 |
| QCOM | 1/1 | 3,097,332 | 67 | 408 | 2025-11-05 / 2026-07-29 | 0 |

网络统计：`request_count=12`、`retry_count=2`、`downloaded_bytes=19,573,518`、`network_executed=true`、`model_calls=0`、`status=completed`；redirect/rate_limit/timeout：本次命令结果未提供，未补造。

10 个 accession/form/raw SHA-256：AMD K `0000002488-26-000018`=`dc4fe1861debf22b74ef63e399070981f5fdcabc83e0bc94a7030c9e21386518`，Q `0000002488-26-000123`=`86500b5f6a6941e2758fc3abca9de77b2a2030f979adceb2da6cef645348450c`；AVGO K `0001730168-25-000121`=`57feb19f73fcfc78b22a476d835283f108c22e8216f4de7b3db39b8e8c8984df`，Q `0001730168-26-000080`=`b7a953ad4a2cd22a8e610f77c3b919c48431497806535d4fccbf96683a7b42d3`；INTC K `0000050863-26-000011`=`7240f6252d0793468493efe434b1c785dd841b46b26dddb77bb960c6b2096aa6`，Q `0000050863-26-000157`=`6750ee732b82561433f4204dff107d65ca6a8c63e4479c7df96d7266afc286d1`；NVDA K `0001045810-26-000021`=`59efa41a63393efa51c9932825923ff9805177b0fc7cd5bb7d0f6762abac09e2`，Q `0001045810-26-000075`=`7c288c7fb2fe257284d815b40508cfaa782fee9f57a1c91bd4743ea5f580dfe7`；QCOM K `0000804328-25-000085`=`32471cc5ff989593805ffcc5b6c4de70cda4c5c284b0a2bc35750050ee4427a9`，Q `0000804328-26-000086`=`da5857ad3e1ee490122d38cd267eccc63b74b0c0d525e164d29f03485e696295`。

Corpus aggregate SHA-256：`45172c8250de63166d9d270e5d3081712881516f8614def07131ea2a9b4f6d27`（按 ticker/accession 排序的五文件 SHA 映射 canonical JSON）；candidate manifest SHA-256：`ed176273d95d197973df538b4ea2282a5f9efb9f8b15d32238c54756ba916276`。SEC 正文可能自带公开联系字符串，仅留 gitignored 本地证据，不回显、不记录具体值，且不等于 User-Agent 泄漏。100 份仍为候选，剩余 90 份未下载；下一步确认离线检索/评测方案。

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

正文下载仍必须显式传入 `--network` 并配置 `FINSIGHT_SEC_USER_AGENT`；缺失 User-Agent、manifest 无效、预算非法、输出路径不安全或身份冲突均在首个网络请求前停止。本轮已完成上述最多 10 份小批量真实正文下载；下一步确认离线检索/评测方案。
