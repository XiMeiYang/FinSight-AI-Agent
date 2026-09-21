# 行情供应商候选调研

核验日期：2026-09-21。以下为官方资料案头核验，不是在线契约测试、价格承诺或生产选型。

| 候选 | 美股/搜索/日线/分钟 | 额度、延迟、频率、历史 | key、调整价、CSV/Excel | 许可/展示 | 建议 |
|---|---|---|---|---|---|
| Alpha Vantage（[官方文档](https://www.alphavantage.co/documentation/)） | 官方文档确认 US equities、symbol search、`TIME_SERIES_DAILY`；分钟端点存在 | 免费层额度、延迟和历史长度需按当前条款/账户实测；本 PoC 默认 `compact`，不承诺免费 `full` 或分钟 | API key；调整价字段与 CSV/Excel 能力需逐端点实测 | 缓存、展示、再分发和项目展示许可未确认 | 推荐低成本日线 PoC，未冻结生产 |
| Massive（原 Polygon.io，[Stocks API](https://polygon.io/docs/stocks)） | 官方资料列 REST/WebSocket 股票、聚合日线/分钟和 ticker 搜索 | 套餐、频率、实时延迟和历史范围未实测 | key；调整价、导出格式未完成契约测试 | 套餐许可/展示权限待核对 | 备选 |
| Financial Modeling Prep（[官方文档](https://site.financialmodelingprep.com/developer/docs)） | 官方资料列 quote、historical price、symbol search；分钟覆盖待确认 | 免费额度、频率、延迟、历史长度待账户实测 | key；调整价、CSV/Excel 导出待实测 | 缓存/再分发和展示条款待核对 | 备选 |
| Finnhub（[官方 API 文档](https://finnhub.io/docs/api)） | 官方资料列 symbol lookup、quote、股票 candle；分钟语义待实测 | 免费额度、频率、延迟、历史范围待核对 | API key；调整价和导出格式待实测 | 免费计划及展示/缓存限制待核对 | 备选 |

所有供应商的免费层、延迟、历史长度、许可及再分发范围均可能随套餐或条款变化；本文件不把网页宣传转述为已验证能力。当前只实现 Alpha Vantage `TIME_SERIES_DAILY` 离线契约，默认不联网；无 key 或未显式启用 runner 时安全停止。
