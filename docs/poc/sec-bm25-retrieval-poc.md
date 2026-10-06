# SEC BM25 离线检索 PoC

## 范围与状态

2026-10-05 在已验收的 10 份真实 SEC filing（5 份 10-K、5 份 10-Q）、399 sections、2,003 chunks 上完成一次完全离线的 BM25 Okapi baseline。corpus aggregate SHA-256 为 `45172c8250de63166d9d270e5d3081712881516f8614def07131ea2a9b4f6d27`；本轮检索流程 `network_executed=false`、`model_calls=0`。

这是词法检索基线，不是完整 RAG。后续已完成本地 Dense Embedding 对照，详见 [SEC Dense Embedding 检索 PoC](sec-embedding-retrieval-poc.md)；向量数据库、RRF、Reranker、LLM 回答、Agent 和前端真实连接仍未实现。

## 可复现实现

- tokenizer `financial-v1` 统一大小写和 Unicode 连字符，保留确定性的字母数字、财务数字、百分比及连字符术语处理；空查询和超过 2,000 字符的查询拒绝。
- BM25 使用 `k1=1.5`、`b=0.75`，IDF 为 `log(1 + (N - df + 0.5) / (df + 0.5))`。
- 建索引前重新验证每个 bundle 的五件套、身份、哈希、citation、Point-in-Time 和全 corpus chunk ID 唯一性。
- 索引使用 JSON/JSONL，不使用 pickle；manifest 记录 corpus、tokenizer、参数、统计和产物 SHA-256。输出以同目录临时目录构建并原子提交，默认不覆盖，完整同源索引安全跳过，冲突或不完整索引失败。
- 搜索在评分前应用 symbol、form 和 as-of 过滤；同分按 symbol、accession、section、chunk index 和 chunk ID 稳定排序。每条结果最多返回 400 字符证据预览。

```bash
PYTHONPATH=src python3 scripts/build_sec_bm25_index.py \
  --corpus .local_data/rag/corpus \
  --output .local_data/rag/indexes/sec-bm25-2026-09-18

PYTHONPATH=src python3 scripts/search_sec_corpus.py \
  --index .local_data/rag/indexes/sec-bm25-2026-09-18 \
  --corpus .local_data/rag/corpus \
  --query "example financial question" --top-k 10
```

## 真实离线索引结果

| 项目 | 实际结果 |
| --- | ---: |
| filing documents | 10 |
| chunks | 2,003 |
| vocabulary | 14,406 |
| average document length | 253.3979 tokens |
| index size | 6,868,992 bytes（文件系统 `du` 口径约 6.55 MiB） |
| build wall time | 0.99 s（单次本机运行） |
| index SHA-256 | `640e2a0f68ec6d633bbe5184bd80502c1db38a08ed8f52adf5f65e25ffc66f02` |

公司 chunks：AMD 416、AVGO 377、INTC 470、NVDA 332、QCOM 408；表单 chunks：10-K 1,369、10-Q 634。真实索引只保存在 gitignored `.local_data`。

## Provisional 诊断评测

本地查询集包含 20 条 `provisional_developer_authored` 查询：每家公司 4 条，10-K 与 10-Q 各 10 条，覆盖业务、风险、MD&A、分部和财务事实。每条 expected chunk、accession 和 section 均基于原文人工检查；没有根据检索结果删除失败或修改 ground truth。

它不是用户真实查询，样本量小，存在开发者构造偏差，不能用于宣称“RAG 准确率”、用户满意度或生产可用性。

| 指标 | 实际结果 |
| --- | ---: |
| Hit@1 | 0.40 |
| Hit@3 | 0.55 |
| Hit@5 | 0.60 |
| Hit@10 | 0.75 |
| MRR@10 | 0.497560 |
| Recall@10 | 0.75 |
| no-result rate | 0.00 |
| failed queries | 0 |
| median query latency | 0.603 ms |
| p95 query latency | 0.982 ms |

5 条查询的指定证据未进入前 10，主要涉及宽泛业务/制造描述、库存比较和分部表达；这些失败保留给下一轮分析。延迟仅为同一进程中已加载索引后的检索计算，不包含进程启动和索引加载。

## 数据与 Git 边界

真实 filing、chunks、索引、查询集、真实 chunk ID 和证据预览全部留在 `.local_data`，不提交 Git。仓库只保存实现、synthetic fixture、测试和不含真实原文的汇总。下一步应先获得用户任务形成的独立查询集，再比较 BM25 与候选语义检索方法；在此之前不扩展剩余 90 份正文。
