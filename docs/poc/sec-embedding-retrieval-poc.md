# SEC Dense Embedding 离线检索 PoC

## 范围与结论

2026-10-06 在已验收的 10 份真实 SEC filing、2,003 chunks 上完成单一预定模型 `BAAI/bge-small-en-v1.5` 的本地 Dense（稠密向量）检索。模型固定 revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`，许可证 MIT，向量维度 384，最大输入长度 512 tokens。用户决定暂缓独立真实查询收集，因此评测继续使用冻结的 20 条 `provisional_developer_authored` 诊断查询；它不是用户真实查询或生产评测集。

本轮结果不支持“Dense 整体优于 BM25”：Dense Hit@10 为 0.70，BM25 为 0.75；Dense 找回原 5 条 BM25 Top-10 失败中的 2 条，同时有 3 条仅 BM25 成功。后续已完成 [固定 Hybrid RRF](sec-hybrid-rrf-retrieval-poc.md) 对照；Reranker、LLM 回答、向量数据库或完整 RAG 尚未实现。

## 固定实现与数据边界

- 使用 Sentence Transformers 官方接口；document 直接编码，query 前置官方 instruction `Represent this sentence for searching relevant passages: `。
- CPU、float32、batch size 32、L2 归一化向量；cosine similarity 使用归一化向量点积的数学等价实现。
- corpus aggregate SHA-256：`45172c8250de63166d9d270e5d3081712881516f8614def07131ea2a9b4f6d27`；冻结查询文件 SHA-256：`2e66af31ba0ef46da30575351d25df9009ce1b7192ee123745b1bf0c2944ca69`。
- 模型只缓存于 `.local_data/models/hub`；真实向量、索引、查询和原文只保存在 gitignored `.local_data`，不提交 Git，也不重新分发模型权重。
- 模型与依赖首次下载阶段使用网络；模型缓存完成后的 index build、search、evaluation 均强制 local-files-only/offline，`network_executed=false`、`llm_calls=0`。没有 SEC、Alpha Vantage、Embedding API 或 LLM API 请求。

索引包含 `manifest.json`、`documents.jsonl`、`embeddings.npy`，NumPy 始终以 `allow_pickle=False` 读取。构建前复用 corpus bundle 的身份、五文件哈希、citation、Point-in-Time 与 chunk ID 唯一性验证；索引校验 shape、float32、finite、归一化、行对齐、模型 revision、corpus provenance 与各产物 SHA-256。临时目录与最终目录同级，原子提交；默认不覆盖，完整同源安全跳过，冲突失败，显式覆盖带恢复。

## 真实索引结果

| 项目 | 实际结果 |
| --- | ---: |
| filing documents | 10 |
| chunks / encoded texts | 2,003 / 2,003 |
| embedding batches | 63 |
| embedding dimension | 384 |
| index size | 7,553,275 bytes |
| build wall time | 96.813 s（单次本机运行） |
| documents SHA-256 | `ea4c1e57b100065a20b3c807a433f5dce7ef8b3eadbcf9db155ab8a4202598c8` |
| embeddings SHA-256 | `35b99ac52073f869b3e6204633cce4ff427ea459eeaefdff5d1cfbf9cdfed936` |
| manifest canonical self-check digest | `fecbbb57bb3bcfdcb8db56a25ee6fff5c7b1a727880c6587e11089a6f1225380` |
| `manifest.json` file SHA-256 | `3b27bc979876c6c12aef7d4e01e0dec47d3324890f3cfbeca62260119daed897` |

依赖实测版本：sentence-transformers 5.7.0、transformers 5.18.0、huggingface-hub 1.33.0、torch 2.7.0、numpy 2.2.6。

## 与 BM25 同口径对照

| 指标 | BM25 | Dense BGE |
| --- | ---: | ---: |
| Hit@1 | 0.40 | 0.30 |
| Hit@3 | 0.55 | 0.55 |
| Hit@5 | 0.60 | 0.60 |
| Hit@10 | 0.75 | 0.70 |
| MRR@10 | 0.497560 | 0.441865 |
| Recall@10 | 0.75 | 0.70 |
| no-result rate | 0.00 | 0.00 |
| median latency | 0.607 ms | 11.212 ms |
| p95 latency | 1.070 ms | 15.082 ms |

延迟仅统计同进程中已加载索引与模型后的检索，不含进程启动和模型加载。20 条查询逐条比较为 Dense 提高 5、持平 9、下降 6；成功交集为两者都成功 12、仅 BM25 3、仅 Dense 2、两者都失败 3。Dense 找回 `amd-inventory-10q` 与 `intc-manufacturing-10k`；仍失败的诊断包括 AMD 风险、INTC 分部、QCOM 业务、QCOM 中国风险和 QCOM 收入变化。失败保留，不修改查询或 expected chunk。

## 可复现命令

```bash
PYTHONPATH=src python3 scripts/build_sec_embedding_index.py \
  --corpus .local_data/rag/corpus \
  --output .local_data/rag/indexes/sec-bge-small-en-v1.5-2026-09-18 \
  --model-revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a \
  --batch-size 32 --cache-folder .local_data/models/hub --offline
```

运行时还应设置 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1` 和 `HF_HUB_DISABLE_TELEMETRY=1`。后续固定 RRF 实验验证了两路互补性，但仍不能从这 20 条开发者查询直接推出生产效果。
