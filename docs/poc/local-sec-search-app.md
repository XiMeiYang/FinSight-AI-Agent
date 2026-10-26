# 本地 SEC 证据检索应用

2026-10-26 当前本机状态：100 份正文、15,925 个片段及新 BM25/Dense 索引已通过严格匹配并由网页检索验证。旧 10 份索引和 2026-10-25 的临时验收目录均不是当前正式启动路径。见[100 份索引验收](sec-100-index-poc.md)。

2026-10-25 历史状态：当时原 BM25/Dense 索引为 10 份/2,003 片段，而 corpus 已有 100 份/15,925 片段；直接混用被来源指纹拒绝。当时仅在 Git 忽略的临时目录完成旧 10 份复验，未改原数据或索引。

后续状态（2026-10-08）：用户已授权在此证据页面增加可选的本机 Ollama 中文回答。证据检索 API 的 `answer_status=not_generated` 保持不变；只有显式启用并由用户点击按钮，新的 `/api/sec/answer` 才调用本地模型。详见[本地 Ollama SEC 问答 PoC](local-ollama-sec-rag.md)。以下原有零 LLM 描述特指默认未启用模式及先前证据检索阶段。

状态（2026-10-08）：已把先前验收的 10 份 SEC filing、2,003 个片段、BM25 索引、本地 BGE Dense 索引与固定无权重 RRF 接入本机网页。根据用户实际检索 NVDA 后的可读性反馈，本轮仅调整确定性的原文句子窗口、结果折叠与接口契约；不改变检索排序或诊断指标。网页显示真实 SEC 证据而非 LLM 答案，不是完整 RAG 或投资建议。

## 数据与运行边界

- 真实语料仍只保存在被 Git 忽略的 `.local_data`；5 家公司为 AMD、AVGO、INTC、NVDA、QCOM，当前本机每家已有 5 份 10-K、15 份 10-Q，共 100 份。早期每家各 1 份的描述仅属于 10 份历史基线。
- 服务复用 `load_index`、`load_dense_index`、`BGEEmbedder`、`search_loaded_hybrid` 和现有 corpus/index 的身份、来源、哈希、Point-in-Time 校验；没有复制检索算法或改变 RRF 参数。
- 运行时固定 `BAAI/bge-small-en-v1.5` revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`，并设置 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`、`HF_HUB_DISABLE_TELEMETRY=1`、`local_files_only=True`。服务第一次使用时加载模型、索引和 corpus，此后复用。
- 应用默认仅监听 `127.0.0.1:8000`；CLI 只接受 loopback host，不提供公网部署。服务没有 SEC、Alpha Vantage、模型下载、Embedding API 或 LLM 请求；用户主动打开来源链接属于浏览器访问 SEC 网站，不是本地检索服务的请求。
- 当前界面其他“演示研究”、自选股、收盘报告、历史复盘仍为 Mock/占位，不能与真实 SEC 证据混同。

## 本机启动

先只读发现已有 corpus、BM25/Dense 索引和 BGE 缓存目录，再显式提供路径；不要猜测路径，也不要把真实文件提交 Git。现有隔离嵌入环境中仅新增 `requirements-app.txt` 的应用依赖，未升级 embedding 依赖。2026-10-07 实际安装版本为 FastAPI `0.142.2`、Uvicorn `0.54.0`，传递依赖包括 Pydantic `2.13.5`、Starlette `1.7.0`。包安装通过 PyPI 联网；它与业务数据联网不同。

采用前于 2026-10-07 核对官方 [FastAPI StaticFiles](https://fastapi.tiangolo.com/tutorial/static-files/)、[FastAPI TestClient](https://fastapi.tiangolo.com/tutorial/testing/) 和 [Uvicorn programmatic settings](https://www.uvicorn.org/settings/) 文档；这些只支持本地静态页面、API 测试和 loopback 服务实现，不代表选择了生产部署方案。

```bash
.local_data/venvs/sec-embedding/bin/python -m pip install -r requirements-app.txt
.local_data/venvs/sec-embedding/bin/python scripts/run_local_app.py \
  --bm25-index .local_data/rag/indexes/sec-bm25-2026-10-26-100 \
  --dense-index .local_data/rag/indexes/sec-bge-small-en-v1.5-2026-10-26-100 \
  --corpus .local_data/rag/corpus \
  --model-cache .local_data/models/hub \
  --model-revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a \
  --host 127.0.0.1 --port 8000
```

打开 <http://127.0.0.1:8000/>。本例路径是本仓库这次只读发现的相对路径；其他机器须先确认本地产物实际存在。真实数据和缓存均不随 Git 分发，没有这些离线产物时应用不能完成检索。

## API 契约

- `GET /api/health`：离线数据模式、检索模式、corpus 截止时间、文档/片段数、覆盖 ticker、模型名称与 revision、`network_executed=false`、`llm_calls=0`。
- `GET /api/securities?q=`：从已加载的真实索引动态统计公司、CIK、表单、文档/片段数量与 corpus 截止时间；可按 ticker 或公司名过滤。可搜索的证券目录与已具备 RAG 语料的公司不是一回事。
- `POST /api/sec/evidence-search`：接受 `symbol`、`question`（3–1000 字符）、可选 `form` (`10-K`/`10-Q`)、`as_of`、`top_k` (1–10)，把相同过滤条件交给已有 Hybrid 检索。请求体上限 16 KiB，超出返回稳定的 413 JSON；未来截止时间、未知公司与非法输入安全拒绝，错误不回显问题、环境路径或 traceback。成功响应含 `status=completed`、`answer_status=not_generated`、`retrieval_mode=hybrid_rrf`、`network_executed=false`、`llm_calls=0`、`evidence`。每条证据保留身份/引用字段及 `retrieved_by`、`bm25_rank`、`dense_rank`、`rrf_score`；`results` 暂作为兼容字段保留，网页只读取 `evidence`，绝不能把它们称作 answer。

`evidence_excerpt` 是从原始 chunk 以问题关键词重合度确定性选择的完整句子窗口，必要时在单词边界截短并标注省略号；同时返回 `excerpt_truncated`、`matched_terms`。这里 `excerpt_truncated=true` 专指所展示的句子或 chunk 边缘片段因边界安全而被截短；仅选择若干完整句子、不展示 chunk 其他句子时为 `false`。它不是摘要、翻译或新生成的事实，原始 chunk、索引和最终排名均不更改。界面默认仅展示前 3 条，其余 4–10 条可展开；公司覆盖默认折叠，BM25/Dense/RRF 和 CIK、accession、chunk 等技术字段放在每条证据的可展开详情。结果区持续提示证据不是答案、排名不代表正确、不构成投资建议及 SEC 链接会离开本机页面。

输入校验与服务异常采用固定脱敏错误，不回显原始请求值、User-Agent、邮箱或本机绝对路径。网页对结果文本做 HTML 转义，并只把允许的 `https://www.sec.gov/Archives/` 链接渲染为外部来源。

## 验证与限制

旧 10 份阶段未运行冻结的 20 条诊断查询评测，没有调 RRF 参数或修改 ground truth。合成 fake-service 单元测试不读取真实 `.local_data`。当时一次 HTTP smoke 的 `/api/health` 为 5 家公司、10 文档、2,003 片段；这不是当前覆盖数。2026-10-26 新 100 份索引的 `/api/health` 为 5 家公司、100 文档、15,925 片段；五家公司各一次通用问题检索均返回 10 条 SEC Archives 证据，`network_executed=false`、`llm_calls=0`。浏览器也验证了新覆盖数和证据卡片。以上仅是连通性验收，不是检索质量评测或真实用户可用性测试。

后续已增加可选本机 Ollama 回答与 E 编号的后端引用映射，但仍未实现 Reranker、全面事实一致性评测、生产级 RAG、行情连接、数据库、自选股后台、邮件或公网部署。证据展示阶段没有新增 SEC 文件，也没有重新评测或调整 RRF；当前应由用户实际核对本地模型回答的每条引用。
