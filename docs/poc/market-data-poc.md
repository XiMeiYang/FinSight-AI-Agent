# Alpha Vantage 日线行情 PoC

状态：已实现离线解析与固定 synthetic fixture 测试，并完成一次用户执行的 NVDA 日线 live smoke；未冻结生产供应商。

适配器位于 `src/finsight_market/alpha_vantage.py`，仅支持建议的 `https://www.alphavantage.co/query`、`TIME_SERIES_DAILY` 日线契约。默认 `outputsize=compact`；`full` 可能需要付费套餐，不能视为免费能力。API key 只从 `FINSIGHT_MARKET_API_KEY` 读取，缺失即停止；日志和请求元数据会脱敏。raw 与 normalized 分离保存，raw 可计算 SHA-256，写入按路径幂等。

标准化结果包含 OHLCV、升序 `as_of`、UTC 日线 `timestamp`、`source`、`source_url`、`retrieved_at`、`currency`（供应商未提供时为空）和可选 `adjusted_close` 字段。解析会拒绝缺失、非数值、负成交量及 high/low 关系错误。429/5xx 有限重试，4xx、超时、空响应和无效 JSON 结构化失败。

测试使用 synthetic fixture，不代表真实市场数据或供应商稳定性。未安装依赖、未连接数据库、未启动监控或定时任务。


## NVDA 真实联网 smoke 记录

用户于 **2026-09-21 13:54:49.165880 UTC** 在本机执行：

```bash
PYTHONPATH=src python3 scripts/run_market_poc.py NVDA --network
```

真实输出记录：HTTP 状态 `200`；响应耗时 `1226.955 ms`；请求次数 `1`；重试次数 `0`；获取日线 `100` 条；规范化文件日期范围为 `2026-04-28` 至 `2026-09-18`；raw SHA-256 为 `aa3108b0138a00e562a40fdc21f9f5ce716524374df939cd62df3e1eecccbb58`。

文件已生成：`.local_data/market/raw/NVDA_2026-09-21T135449.165880_0000.json` 和 `.local_data/market/normalized/NVDA_2026-09-21T135449.165880_0000.json`；`.local_data/` 已被 Git 忽略。未出现限速、超时或其他异常，API Key 在输出中保持 `[REDACTED]`。本次只验证日线，不能用于分钟级实时监控；成功不代表长期稳定性，Alpha Vantage 未冻结为生产供应商，K线前端和 Excel 导出尚未实现。

官方支持页核验日期为 **2026-09-21**：[Alpha Vantage Support](https://www.alphavantage.co/support/)。页面通常说明免费股票 API 为每天 25 次请求，实时及 15 分钟延迟美股行情属于付费能力；本次账户实际表现优先于网页描述，但一次请求不能推断长期额度或稳定性。
