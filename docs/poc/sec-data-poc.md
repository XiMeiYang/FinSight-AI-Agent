# SEC EDGAR / Company Facts PoC

状态：离线实现已写入并通过固定 fixture 验证；已完成一次用户执行的 NVDA 低频实时 smoke，但尚未接入生产流程。实现位于 `src/finsight_sec/`，固定 synthetic fixture 位于 `tests/fixtures/`。官方资料核验日期：2026-09-21。

官方资料：[EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)、[Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)、[SEC rate control](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits)。代码生成的 filing URL 使用 SEC Archives 前缀。Company Facts 的 XBRL 边界、公平访问、CORS 和 User-Agent 要求已核验；实时 smoke 结果见下文，生产接入仍未完成。

覆盖 ticker→10 位 CIK、Submissions 读取与 10-K/10-Q/8-K 筛选、归档 URL、Company Facts 规范化、`as_of` 过滤、原始响应 SHA-256、raw/normalized 分离，以及 User-Agent 强制、限速、超时、有限重试和 HTTP 错误分类。ticker 映射使用 `https://www.sec.gov/files/company_tickers.json`；Submissions 与 Company Facts 使用 `https://data.sec.gov`。每个已发出的 HTTP 请求记录 requested/final URL、状态、耗时、encoding、fetched_at、attempt/retry 计数及重试原因；初始和重定向最终 URL 均属于 SEC 白名单，阻断请求不会伪造 HTTP 成功 metadata。请求默认声明 `Accept-Encoding: identity`，若服务端仍返回 gzip 则显式解压。未设置 `FINSIGHT_SEC_USER_AGENT` 时拒绝网络请求；测试默认不联网。

当前历史边界：只使用 Submissions 的 `recent` 列表；较旧历史文件未自动下载，需后续明确设计和离线验证后再扩展。`as_of` 仅按 SEC 公布字段过滤，不代表完整 Point-in-Time 历史覆盖。

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/sec_poc_smoke.py
```

固定 synthetic 数据只证明解析和边界逻辑，不证明 SEC 在线可用性、许可、额度或生产质量。真实 smoke check 需用户明确配置 User-Agent 后另行执行。

本轮离线测试已执行并通过；实时 smoke 已由用户在本机执行并如实记录在下文。

## NVDA 真实联网 smoke 记录

用户于 **2026-09-21 11:46:07–11:46:14（输出中的 UTC 时间）** 在本机执行：

```bash
PYTHONPATH=src python3 scripts/run_sec_poc.py --ticker NVDA
```

结果为成功，且 `network_executed: true`：

| 阶段 | 结果 | HTTP 状态 | 耗时 |
| --- | --- | ---: | ---: |
| ticker mapping | NVDA → CIK 成功 | 200 | 1740.988 ms |
| submissions | 成功 | 200 | 1092.984 ms |
| companyfacts | 成功 | 200 | 4211.057 ms |
| filing | 成功 | 200 | 782.629 ms |

本次共 **4 次 HTTP 请求**，**0 次重试**；输出中没有出现限速、超时或其他异常。识别结果为 `CIK 0001045810`，Submissions 的 `recent` 列表筛选出 **87** 条目标表单，Company Facts 规范化得到 **27281** 条事实记录。下载文件大小为 **29297 bytes**，SHA-256 为 `57c98a6c81c31e687dbaab7a958b919d3f9e85af321847d4393c04ad9d291862`。

本次 `.local_data/sec` 检查到 `raw/` 与 `normalized/` 各 **4** 个文件，分别对应 ticker mapping、submissions、Company Facts 和首份 filing；该目录已被 `.gitignore` 忽略，原始 SEC 文件和本地 User-Agent 均未加入 Git。此次结果只证明一次低频 NVDA smoke 成功，不代表完整历史、持续可用性、许可、缓存/再分发范围或生产质量已经验证。
