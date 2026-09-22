# ResearchSnapshot 离线 PoC

状态：已完成离线 synthetic 契约与 fixture 测试。本轮进入 MVP 基础实现，但不是完整 MVP。

## 目标

将 Alpha Vantage 日线规范化结果与 SEC Company Facts/Submissions 规范化结果组合为一个统一、可追溯、可测试的 `ResearchSnapshot` JSON。构建过程不联网、不读取 API Key、不读取 `.local_data`，也不装配真实 NVDA 本地文件。

## 输入与输出

`build_research_snapshot` 接收 symbol、行情、Company Facts、filings、`as_of`、`data_mode` 和可注入时钟。支持 `synthetic` 与 `saved_snapshot`，不支持 `live`。输出包含 schema 信息、security、market_data、sec_filings、sec_facts、deterministic summary、sources、data_quality 和 run_record。

CLI fixture 示例：

```bash
PYTHONPATH=src python3 scripts/build_research_snapshot.py TEST --fixture --as-of 2024-12-31
```

默认输出标准输出；只有传入 `--output PATH` 才写文件。fixture 中的公司名保留为 `Synthetic Example Corp`，不会冒充 NVDA。

## Point-in-Time 与状态规则

行情按日期升序并过滤到 `as_of`；SEC 文件按公开/申报时间过滤；事实必须有 `available_at` 且不晚于 `as_of`，缺少该字段会被排除。缺失值保持 `null` 或空列表，不转换为零。`completed` 表示行情与至少一种 SEC 证据存在；只有部分数据时为 `partial`；完全没有行情和 SEC 数据时为 `failed`。过滤数量写入 `data_quality.point_in_time_filtered_count`。

## 运行记录与来源

快照的 `run_record.network_executed` 始终为 `false`，`model_calls` 为 0。来源记录保留 provider、URL、时间和已有 SHA-256；缺失哈希保持 `null`。确定性摘要只统计已有数据，不作涨跌预测或投资建议。

## 测试

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall -q src tests scripts
node --check prototype/app.js
git diff --check
```

## 已知限制

本轮没有真实 NVDA 文件装配、真实 Excel、数据库、RAG、LLM、Agent、监控、前端真实数据接入或部署。原型可用性测试由用户决定暂缓，仍未执行，后续可以补做，不能写成已验证成功。当前 fixture 仅验证契约和离线逻辑，不代表真实数据质量或生产稳定性。

## 下一步

使用经过审查的本地保存 NVDA 快照进行装配测试，再评估 Excel/API 契约；继续保持网络、密钥和真实文件与 synthetic fixture 隔离。
