# 100 份本地 SEC 正文索引匹配验收

2026-10-26 本机离线验收。以下是这一台电脑上被 Git 忽略的 `.local_data` 产物，不随仓库克隆分发。没有重新下载 SEC 正文、行情或模型。

## 只读盘点与边界

- `.local_data/rag/corpus`：100 份唯一 filing bundle、5 家公司（AMD、AVGO、INTC、NVDA、QCOM），每家 5 份 10-K 和 15 份 10-Q，共 25 份 10-K、75 份 10-Q、15,925 个片段。filing date 为 2021-10-22 至 2026-09-10；每份 bundle 的截止时间均为 `2026-09-18T23:59:59Z`。
- 现有严格加载器逐份核验身份、文件 SHA-256、SEC Archives 来源 URL、公开时间与截止时间；候选清单 `semiconductor-candidates-2026-09-18.json` 的 SHA-256 为 `521a0701d5f1dac140554a280c16c5fe63620ee55565107db88420c6505adb2d`，含 5 家公司，ticker/CIK 与五个公司目录一致，目录各有 20 份 filing。本轮未跳过或放宽任何校验。语料 aggregate SHA-256 为 `99019f961627e03ecf068ca4d9fb5507b05dbfa5f4a31d9c57fa13d0f3037d87`；chunks SHA-256 为 `a9a6ef6800ec57c1b4e7de2d5a57a3d622c0c0296e48d37dbb555662f63904ab`。
- 历史 BM25 索引 `.local_data/rag/indexes/sec-bm25-2026-09-18` 的 manifest 文件 SHA-256 为 `b46472fdefe92e3d8929fcaec66b711b271d3d3fd124a8ff09354c1183a35855`；历史 Dense 索引 `.local_data/rag/indexes/sec-bge-small-en-v1.5-2026-09-18` 为 `3b27bc979876c6c12aef7d4e01e0dec47d3324890f3cfbeca62260119daed897`。两者仅对应 10 份、2,003 个片段，aggregate SHA-256 为 `45172c8250de63166d9d270e5d3081712881516f8614def07131ea2a9b4f6d27`。旧索引保留原样，与当前 100 份语料混用会被拒绝。

## 新建的本机正式索引

| 类型 | 相对目录 | 文档 / 片段 | 构建耗时 | 目录大小 | manifest 文件 SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| BM25 | `.local_data/rag/indexes/sec-bm25-2026-10-26-100` | 100 / 15,925 | 7.83 秒 | 55,585,606 bytes | `611bd5a7fadb3ffa42031bab276c48320da388fb5467bda7d4a3427f8413cc71` |
| Dense | `.local_data/rag/indexes/sec-bge-small-en-v1.5-2026-10-26-100` | 100 / 15,925 | 859.35 秒 | 60,254,895 bytes | `cd71d6d2d925440dbc478d0c18fdb0cfaff1a35f53d9a44e71d1beb2dfaedde5` |

首次构建前的资源采样没有留存，因此又在第二次构建前记录磁盘可用约 67 GiB、物理内存约 18 GB、系统报告空闲内存比例 32%，并原子重建**新**目录；最后一次 BM25 重建前再次确认 66 GiB 可用、内存空闲比例 59%。表中是最终文件哈希与最后一次构建耗时；第一次构建的 manifest SHA 不再作为当前产物使用。

BM25 沿用 `financial-v1` tokenizer、`k1=1.5`、`b=0.75`，最终数据索引 SHA-256 为 `37d5c13bacdf62bd25ce854bc5665a8ee30644d5e55a468194b88da88607930f`。Dense 沿用 `BAAI/bge-small-en-v1.5` 固定 revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`、CPU、float32、384 维、归一化和现有 query instruction；通过本地缓存及 `--offline` 构建，未下载模型，矩阵 SHA-256 为 `7063fc3538cf6ccd0a7380ffaf4a0021e8e94868611bd0376d2203d077d2a028`。两个索引的 aggregate/chunks/identity 指纹一致；`load_index`、`load_dense_index` 和 `validate_compatible_indexes` 均通过。重建只对新目录使用原子 `--overwrite`，**旧 10 份索引从未覆盖或删除**，其 manifest SHA 前后不变。

## 可复制的本机启动命令

在仓库根目录运行，前提是本机已有对应的 `.local_data` 语料、索引、模型缓存及隔离 Python 环境。其他机器应先自行构建匹配索引，不能将 Git 中的文档当作本地产物。

```bash
PYTHONPATH=src .local_data/venvs/sec-embedding/bin/python scripts/run_local_app.py \
  --bm25-index .local_data/rag/indexes/sec-bm25-2026-10-26-100 \
  --dense-index .local_data/rag/indexes/sec-bge-small-en-v1.5-2026-10-26-100 \
  --corpus .local_data/rag/corpus \
  --model-cache .local_data/models/hub \
  --model-revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a \
  --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000/`。默认纯检索，`/api/health` 的 `ollama_enabled=false`、`local_model_calls=0`。仅在用户需要本地中文回答时，在命令末尾显式加入 `--enable-ollama --ollama-model qwen3:4b`；模型调用只在网页点击“生成中文回答”后发生。

## 本轮验收

- 新索引服务的 `/api/health` 报告 5 家公司、100 文档、15,925 片段、截止时间 `2026-09-18T23:59:59Z`、`network_executed=false`。AMD、AVGO、INTC、NVDA、QCOM 各完成一次证据检索，每次返回 10 条；来源 URL 均为 SEC Archives，`answer_status=not_generated`、`llm_calls=0`。浏览器也实际显示了新覆盖数和证据卡片。
- 默认不开 Ollama 的网页检索完成，模型调用为 0。为核对原子重建前后均可用，本轮在两个不同本机服务上各主动点击一次 NVDA 回答，合计 **2 次本地模型调用**，均返回非空中文 `completed`；首次报告生成耗时 14,744 ms，最终索引版本为 **16,773 ms**、调用 1 次、外部业务数据请求 0。最终版本点击 E7 后展开并定位到本次检索的第 7 条 SEC 证据。E 引用由后端从本次结果映射，链接限定为 SEC Archives。此为连通性与引用映射验收，**不是**逐句事实一致性或投资判断质量评测。
- 本轮 SEC 请求 0、Alpha Vantage 请求 0、模型下载请求 0。现有完整自动测试 231 项通过；`compileall`、`node --check`、`git diff --check` 通过。真实正文、索引、模型文件均留在 `.local_data`，`git ls-files .local_data` 为空。

旧 20 条冻结诊断集仅针对旧 10 份语料；其 Hit@10、MRR@10 不适用于本次 100 份索引。本轮没有改 ground truth，也没有重新评测检索质量。后续如需评估，须另建或复核适用于新版语料的查询与标注。
