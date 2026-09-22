# ResearchSnapshot 离线 PoC

状态：已完成离线 synthetic 契约与 fixture 测试。本轮进入 MVP 基础实现，但不是完整 MVP。

## 目标

将 Alpha Vantage 日线规范化结果与 SEC Company Facts/Submissions 规范化结果组合为一个统一、可追溯、可测试的 `ResearchSnapshot` JSON。synthetic 构建过程不联网、不读取 API Key；saved_snapshot 模式只读取用户显式指定的 `.local_data` 文件。当前已完成一次真实 NVDA 本地离线装配。

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

本轮已完成一次真实 NVDA 文件离线装配；真实 Excel、数据库、RAG、LLM、Agent、监控、前端真实数据接入或部署仍未完成。原型可用性测试由用户决定暂缓，仍未执行，后续可以补做，不能写成已验证成功。当前 fixture 仅验证契约和离线逻辑，不代表真实数据质量或生产稳定性。

## 下一步

下一步评估 Excel/API 契约，并继续保持网络、密钥和真实文件与 synthetic fixture 隔离。

## 证券身份安全边界

2026-09-23 修复了跨证券混合风险：symbol、CIK 和每根行情记录的 symbol 现在采用 fail-closed 校验；CIK 统一为十位字符串，非法或不一致会拒绝生成快照。公司名、交易所和币种按明确优先级合并，弱字段冲突会阻止静默合并。该修复仍未产生网络请求；真实 NVDA 装配已通过显式本地文件完成，但不代表联网或生产稳定性。

## 2026-09-23：真实 NVDA 本地离线装配

已使用此前联网 PoC 保存的 `.local_data` 文件，通过显式路径完成一次 `saved_snapshot` 装配。该运行没有新增网络请求，输出仍位于被忽略的 `.local_data/research/snapshots/`，真实输入和生成快照不进入 Git。`retrieved_at` 表示文件采集时间，`as_of` 表示快照分析截止时间，两者不等价。本次成功不代表长期稳定性；Excel、API、数据库、RAG、LLM、Agent、前端连接和部署仍未完成。
