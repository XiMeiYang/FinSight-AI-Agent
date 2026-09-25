# ResearchSnapshot Excel 导出

当前实现把已保存的 `ResearchSnapshot` JSON 离线导出为 `.xlsx`，用于 P0 闭环中的证据查看和文件交付。导出器只读取快照，不联网、不读取 API Key、不调用 LLM，也不补写缺失数字；`null` 和缺失说明会保留为缺失状态。

## 工作表

生成文件按固定顺序包含 `Overview`、`Market_Daily`、`SEC_Filings`、`SEC_Facts`、`Sources`、`Data_Quality` 和 `Run_Record` 七张工作表。`Overview` 展示证券身份、截止时间、最新保存行情、SEC 计数、数据质量和限制；明细表保留来源、公开/事件时间、采集时间、币种、单位、URL、版本哈希和输入文件等可用元数据。

## CLI

```bash
PYTHONPATH=src python3 scripts/export_research_excel.py \
  .local_data/research/snapshots/NVDA_snapshot.json \
  --output .local_data/research/exports/NVDA.xlsx
```

输入必须是离线快照，且 `run_record.network_executed` 必须是布尔值 `false`。真实 `.local_data` 文件只用于本地验证并保持 Git 忽略；synthetic fixture 可用于自动测试，但不会冒充真实数据。

实现使用工作区随附的 `@oai/artifact-tool` 运行时，Python 模块负责契约校验和 CLI，`scripts/build_research_excel.mjs` 负责工作簿生成。当前未实现公式驱动的金融计算、图表或数据库导出；本文件是快照字段的可追溯导出，不是完整报告。
