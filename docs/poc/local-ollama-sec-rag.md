# 本地 Ollama SEC 问答 PoC

## 2026-10-26 当前本机索引

100 份 SEC 正文和 15,925 个片段已在新目录建立匹配的 BM25/Dense 索引，严格加载与五家公司网页证据检索通过；默认不开 Ollama 时模型调用为 0。为核对原子重建前后均可用，本轮分别主动点击一次 NVDA 回答，合计 2 次本地模型调用，均返回中文 `completed`；最终索引版本报告生成耗时 16,773 ms、本次调用 1 次、SEC/Alpha Vantage 请求 0，E7 回跳本次 SEC Archives 证据。此为连通性和引用映射验证，尚未完成人工逐句事实一致性评测。新目录和可复制命令见[100 份索引验收](sec-100-index-poc.md)；下文 2026-10-25 的临时 10 份目录以及更早“剩余 90 份”均为历史记录。

## 2026-10-25 复验环境说明

本机当前 `.local_data/rag/corpus` 已有 100 份正文、15,925 个片段，旧 BM25/Dense 索引仍对应 10 份正文、2,003 个片段。读取服务按语料 SHA-256 拒绝直接混用，返回 `offline retrieval is not ready`，这是预期的完整性保护；不能绕过指纹校验或把这次启动记成成功问答。为复验旧检索与问答功能，验收仅从现存本地文件复制旧索引清单中的 10 份到被 Git 忽略的临时目录，并用相同 BM25、Dense、模型版本与 RRF 参数在该目录生成临时匹配索引。正式语料、既有索引和冻结评测集均未修改，未向 SEC 或 Alpha Vantage 发起请求。当前真实正文已达到 100 份，因此下文“剩余 90 份”是 2026-10-08 的历史记录，不是当前本地状态。

同日真实本机复验：`qwen3:4b` 已安装，`/api/tags` 报告 digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`；本轮没有下载模型。NVDA 问题 `What are the main demand and supply risks discussed in the filing?` 在网页主动点击后返回非空中文 `completed`，耗时 13,369 ms；点击 E7 会展开后 7 条并定位到第 7 条。另一次相同问题的 API 检查返回 `completed`、6 条引用，耗时 5,998 ms，引用 ID 均来自本次 evidence，链接均为 SEC Archives。AMD 问题 `What demand and supply risks are described in the filing?` 首次网页回答因输出未通过证据校验而被拒绝，原 10 条证据仍可查看；同问题再次本地调用返回 `completed`、8 条引用，耗时 10,313 ms。INTC 问题 `What supply and manufacturing risks are described in the filing?` 一次调用被同样的输出校验拒绝。上述 5 次真实 `/api/chat` 调用中，每次的 `local_model_calls=1`、`llm_calls=1`、`external_network_executed=false`；失败结果未当作成功。SEC 与 Alpha Vantage 的本轮新请求均为 0。结果显示模型输出并非每次都满足契约，且引用编号正确不等于逐句事实一致性已验证。

默认不开 `--enable-ollama` 的独立服务复验：`/api/health` 显示 `ollama_enabled=false`、`local_model_calls=0`；`/api/sec/evidence-search` 正常返回 2 条 AMD 证据与 `answer_status=not_generated`，回答接口返回 `disabled`。浏览器在 390px 与 1280px 宽度下页面整体均无横向溢出，AMD 失败提示出现时 10 条证据卡片仍在。实际停止用户的 Ollama 服务未执行；服务不可用的错误分类由 fake-client 自动测试覆盖。

状态（2026-10-08）：在现有离线 Hybrid SEC 证据检索网页上增加由用户主动触发的本机 Ollama 中文回答。检索仍使用原 BM25、Dense BGE 与固定 RRF；没有修改索引、语料、冻结查询集或评测参数。此闭环是本地 PoC，不是生产级金融研究系统。

## 使用方式与边界

先按[本地 SEC 检索应用](local-sec-search-app.md)发现并显式提供本机 corpus、BM25/Dense 索引和 BGE 缓存路径。安装 `requirements-app.txt` 后，用原启动命令加 `--enable-ollama --ollama-model qwen3:4b`。不加开关时，网页继续只做证据检索，`POST /api/sec/answer` 返回 `disabled`，启动过程不连接 Ollama。服务只绑定 loopback；Ollama 地址固定为 `http://127.0.0.1:11434`，不使用代理、不跟随重定向。

```bash
PYTHONPATH=src .local_data/venvs/sec-embedding/bin/python scripts/run_local_app.py \
  --bm25-index .local_data/rag/indexes/sec-bm25-2026-10-26-100 \
  --dense-index .local_data/rag/indexes/sec-bge-small-en-v1.5-2026-10-26-100 \
  --corpus .local_data/rag/corpus \
  --model-cache .local_data/models/hub \
  --model-revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a \
  --host 127.0.0.1 --port 8000 --enable-ollama --ollama-model qwen3:4b
```

这些路径是本仓库这次只读发现的相对路径，其他机器须先核对实际产物；模型权重不随 Git 分发。若本机尚无 `qwen3:4b`，需用户明确授权模型下载，不能把下载称为离线运行。

网页先调用 `/api/sec/evidence-search` 展示真实证据。用户点击“生成中文回答（本地模型）”后，`/api/sec/answer` 重新执行相同的服务端检索，不接受浏览器提交的证据或来源 URL。最多取前 10 条，按原 Hybrid 排名赋予 E1–E10，在总字符预算内发送公司、表单、日期、accession、章节和原文句子窗口；BM25/Dense/RRF 分数不进入模型。无证据时不调用模型。用户问题和 SEC 文本都视为不可信数据，系统提示要求忽略其中的指令，只依据证据回答，证据不足时明确说明，不给投资建议。

本地客户端先用官方 `GET /api/tags` 确认模型和 digest，再用 `POST /api/chat`，提交 `stream=false`、`think=false` 及 JSON Schema `format`。服务端验证回答状态、中文直接回答、每个要点的引用 ID、空/重复/未知 ID、非法 JSON、截断响应和伪造 URL；引用的 chunk、ticker、CIK、表单、日期、accession 与 SEC Archives 链接仅从本次检索结果重新映射。网页只用 DOM `textContent` 呈现模型文本，引用按钮展开并滚动到原证据卡片，保留证据列表和 SEC 原始链接。模型不可用、未安装、超时或无效输出时，证据检索仍可使用。

`generation` 区分 `local_model_calls`、`llm_calls` 与 `external_network_executed`。本机 Ollama 调用是实际 LLM 调用，但不是 SEC/Alpha Vantage 外部数据请求。模型下载与离线运行分别记录；模型权重、真实 SEC 文本、索引和用户问题不进入 Git。

## 验证与局限

单元测试全部使用 fake Ollama 和 synthetic SEC 片段，不读取 `.local_data`。真实验收需在 Ollama 与指定模型可用时，使用现有本地语料分别问 NVDA 和另一家公司，并核对回答、引用映射、模型 digest、调用/耗时和网页跳转。测试和实测结果以本轮执行记录为准；一次成功不等于事实一致性评测或用户可用性验证。

2026-10-08 本机实测：原有 Ollama 已安装但缺少 `qwen3:4b`，依用户授权仅执行一次 `ollama pull qwen3:4b`（约 2.5 GB）并成功；模型 digest 为 `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`。这次下载确实使用外网，不能与后续离线业务运行混同。以已有 10 份 SEC 文件、2,003 chunks 对 NVDA 与 AMD 的需求/供应风险问题验收，均在网页返回非空中文 `completed` 回答，各次本地模型调用为 1、外部业务数据请求为 0；模型生成耗时分别为 11,429 ms、13,561 ms。NVDA 回答引用了 E1/E2/E3/E7/E10，AMD 回答引用了 E2/E3/E4/E6/E8；引用由本次检索 evidence 后端映射，SEC URL 均在允许的 Archives 地址内。浏览器点击 NVDA `[E7]` 后，第 4–10 条分组展开并高亮第 7 名卡片。首次真实 NVDA 尝试曾因模型输出混入内联编号或空直接回答被严格拒绝；修复提示与重复编号处理后才得到通过，拒绝不能计作成功。此实测不代表模型每次都稳定或逐句语义完全正确，仍需人工核查。

2026-10-08 当时的完整 synthetic 单元测试在隔离应用环境与 bundled Python 包路径结合下共 220 项通过、0 skip；这是历史记录，不是当前版本的测试总数。当时系统 Python 缺 `openpyxl` 因而失败，bundled Python 单独运行则跳过 17 项应用依赖测试。`compileall`、`node --check` 与 `git diff --check` 当时通过。浏览器在桌面 1280px 和窄屏 390px 视口均未出现横向溢出；页面刷新后回到未生成状态，证据检索仍可重新执行。

2026-10-25 当前版本复验：隔离应用 Python 加载已有 bundled `openpyxl` 后执行 `python -m unittest discover -s tests -p 'test_*.py' -q`，**231 项通过，0 skip**；独立只读验收官亲自复跑同一完整测试。系统 `python3 -m unittest discover -s tests -p 'test_*.py' -q` 为 221 项、1 个 import error、17 skip，错误是缺少 `openpyxl`，不能写成通过。新增回归测试覆盖模型在局限字段写入买卖建议、收益保证和无引用英文事实的情况；后端改用固定中文局限，危险原文不会展示。`compileall`、`node --check` 和 `git diff --check` 通过。

仍未实现 Reranker、完整事实一致性评测、多 Agent、数据库、公网部署或生产级投资研究。文档中的“本地问答”只指用户主动触发、结构化校验与确定性引用映射的最小 PoC。

接口依据（2026-10-08 核对）：[Ollama Chat API](https://docs.ollama.com/api/chat)、[模型列表 API](https://docs.ollama.com/api/tags)、[结构化输出](https://docs.ollama.com/capabilities/structured-outputs)。
