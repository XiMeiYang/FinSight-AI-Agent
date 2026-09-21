# SEC EDGAR / Company Facts PoC

状态：离线实现已写入并通过固定 fixture 验证；实时 SEC 集成未执行。实现位于 `src/finsight_sec/`，固定 synthetic fixture 位于 `tests/fixtures/`。官方资料核验日期：2026-09-21。

官方资料：[EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)、[Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)、[SEC rate control](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits)。代码生成的 filing URL 使用 SEC Archives 前缀。Company Facts 的 XBRL 边界、公平访问、CORS 和 User-Agent 要求已核验；实时请求未执行。

覆盖 ticker→10 位 CIK、Submissions 读取与 10-K/10-Q/8-K 筛选、归档 URL、Company Facts 规范化、`as_of` 过滤、原始响应 SHA-256、raw/normalized 分离，以及 User-Agent 强制、限速、超时、有限重试和 HTTP 错误分类。ticker 映射使用 `https://www.sec.gov/files/company_tickers.json`；Submissions 与 Company Facts 使用 `https://data.sec.gov`。每个已发出的 HTTP 请求记录 requested/final URL、状态、耗时、encoding、fetched_at、attempt/retry 计数及重试原因；初始和重定向最终 URL 均属于 SEC 白名单，阻断请求不会伪造 HTTP 成功 metadata。请求默认声明 `Accept-Encoding: identity`，若服务端仍返回 gzip 则显式解压。未设置 `FINSIGHT_SEC_USER_AGENT` 时拒绝网络请求；测试默认不联网。

当前历史边界：只使用 Submissions 的 `recent` 列表；较旧历史文件未自动下载，需后续明确设计和离线验证后再扩展。`as_of` 仅按 SEC 公布字段过滤，不代表完整 Point-in-Time 历史覆盖。

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/sec_poc_smoke.py
```

固定 synthetic 数据只证明解析和边界逻辑，不证明 SEC 在线可用性、许可、额度或生产质量。真实 smoke check 需用户明确配置 User-Agent 后另行执行。

本轮离线测试已执行并通过；实时 SEC 请求未执行。
