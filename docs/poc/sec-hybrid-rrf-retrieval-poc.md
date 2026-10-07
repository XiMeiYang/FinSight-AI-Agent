# SEC Hybrid RRF 离线检索 PoC

## 范围与固定方案

2026-10-07 在已验收的 10 份 SEC filing、2,003 chunks 上完成完全离线的 Hybrid Retrieval。方案在实验前固定为无权重 Reciprocal Rank Fusion（RRF）：BM25 与 Dense 各取 50 个候选，`k=60`，权重均为 1，最终默认返回 10 条；没有参数扫描、权重调优或原始分数混合。

公式为 `1/(60 + rank_bm25) + 1/(60 + rank_dense)`，缺失一路的贡献为 0。原始 BM25 与 cosine 分数只保留作审计，不参与融合排序。融合前，两路分别应用相同的 symbol、form 与 as-of 过滤；以 chunk ID 去重并验证 corpus、身份、文本、Point-in-Time、BM25 tokenizer、Dense model revision 和离线状态。

用户决定暂缓独立真实查询收集。本轮仍使用 SHA-256 为 `2e66af31ba0ef46da30575351d25df9009ce1b7192ee123745b1bf0c2944ca69` 的 20 条 `provisional_developer_authored` 诊断查询，结果不是用户真实效果或生产准确率。

## 三路实际结果

| 指标 | BM25 | Dense | Hybrid RRF |
| --- | ---: | ---: | ---: |
| Hit@1 | 0.40 | 0.30 | 0.30 |
| Hit@3 | 0.55 | 0.55 | 0.50 |
| Hit@5 | 0.60 | 0.60 | 0.70 |
| Hit@10 | 0.75 | 0.70 | 0.85 |
| MRR@10 | 0.497560 | 0.441865 | 0.461667 |
| Recall@10 | 0.75 | 0.70 | 0.85 |
| no-result rate | 0.00 | 0.00 | 0.00 |
| median latency | 0.973 ms | 12.294 ms | 13.497 ms |
| p95 latency | 1.314 ms | 21.445 ms | 22.612 ms |

RRF 融合本身 median 0.254 ms、p95 0.279 ms。延迟是模型和索引均已加载后的单次本机诊断，不含进程启动、模型加载和首次下载；Dense query embedding 与矩阵相似度无法在当前结构中可靠拆开，因此只报告 Dense 总耗时。

Hybrid 相对 BM25 为提高 6、持平 10、下降 4；相对 Dense 为提高 8、持平 9、下降 3。三路均命中 12 条，仅 Hybrid 命中 1 条，Hybrid 失败 3 条，三路均失败 2 条。

Hybrid 找回 3 个 BM25 Top-10 失败，并找回 3 个 Dense Top-10 失败。它保留 Dense 独有的 2/2 条（AMD inventory、INTC manufacturing），但只保留 BM25 独有的 2/3 条；`qcom-china-risk-10k` 从 BM25 第 8 名降到 Hybrid 第 12 名。Hybrid 的三个 Top-10 失败为 `intc-segments-10q`、`qcom-business-10k` 和 `qcom-china-risk-10k`。

因此，Hybrid 提高了 Hit@10 与 Recall@10，但 Hit@1、Hit@3 和 MRR@10 没有超过 BM25，也没有完整保留 BM25 的精确匹配优势。当前证据支持“两路具有互补性”，不支持“Hybrid 全面优于最佳单路”。失败同时反映融合排序、chunk 边界和当前小 corpus 的限制，不能仅归因于一种方法。

## 运行边界与产物

运行强制要求 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`、`HF_HUB_DISABLE_TELEMETRY=1` 和 CLI `--offline`。SEC、Alpha Vantage、模型下载、Embedding API、LLM 与遥测请求均为 0，`model_calls=0`。

完整结果只保存在 `.local_data/rag/evaluation/sec-hybrid-rrf-provisional-2026-09-18.json`，大小 53,099 bytes，SHA-256 为 `ecc192da7e828ba4701cc1d20de20789acdb2d08c131ea04dbe6f7fc639a76bb`，不提交 Git。结果内记录冻结查询、corpus、BM25、Dense 产物与模型 revision 的 provenance；仓库仅记录实现、synthetic 测试和本汇总，不包含真实查询、chunk ID 或证据文本。

本轮没有建立第三份索引，也未实现 Reranker、LLM 回答、前端接入或完整 RAG。下一步若继续，应先分析三个 Hybrid 失败及一个 BM25 独有证据丢失，再决定是否进入固定 Reranker 实验；不能在当前诊断集上反复调 RRF 参数。
