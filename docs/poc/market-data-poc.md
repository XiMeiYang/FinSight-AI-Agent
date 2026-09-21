# Alpha Vantage 日线行情 PoC

状态：已实现离线解析与固定 synthetic fixture 测试；未执行行情 live 请求，未冻结生产供应商。

适配器位于 `src/finsight_market/alpha_vantage.py`，仅支持建议的 `https://www.alphavantage.co/query`、`TIME_SERIES_DAILY` 日线契约。默认 `outputsize=compact`；`full` 可能需要付费套餐，不能视为免费能力。API key 只从 `FINSIGHT_MARKET_API_KEY` 读取，缺失即停止；日志和请求元数据会脱敏。raw 与 normalized 分离保存，raw 可计算 SHA-256，写入按路径幂等。

标准化结果包含 OHLCV、升序 `as_of`、UTC 日线 `timestamp`、`source`、`source_url`、`retrieved_at`、`currency`（供应商未提供时为空）和可选 `adjusted_close` 字段。解析会拒绝缺失、非数值、负成交量及 high/low 关系错误。429/5xx 有限重试，4xx、超时、空响应和无效 JSON 结构化失败。

测试使用 synthetic fixture，不代表真实市场数据或供应商稳定性。未安装依赖、未连接数据库、未启动监控或定时任务。
