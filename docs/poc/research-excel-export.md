# ResearchSnapshot Excel 导出

当前实现把已保存的 `ResearchSnapshot` JSON 通过 Python `openpyxl` 离线导出为 `.xlsx`，用于 P0 闭环中的证据查看和文件交付。导出器只读取快照，不联网、不读取 API Key、不调用 LLM，也不补写缺失数字；`null` 和缺失说明会保留为缺失状态。输出先写入同目录临时文件，重新打开校验七张表后再原子替换目标文件。

## 工作表

生成文件按固定顺序包含 `Overview`、`Market_Daily`、`SEC_Filings`、`SEC_Facts`、`Sources`、`Data_Quality` 和 `Run_Record` 七张工作表。`Overview` 展示证券身份、截止时间、最新保存行情、SEC 计数、数据质量和限制；明细表保留来源、公开/事件时间、采集时间、币种、单位、URL、版本哈希和输入文件等可用元数据。

## CLI

```bash
PYTHONPATH=src python3 scripts/export_research_excel.py \
  .local_data/research/snapshots/NVDA_snapshot.json \
  --output .local_data/research/exports/NVDA.xlsx
```

输入必须是离线快照，且 `run_record.network_executed` 必须是布尔值 `false`。真实 `.local_data` 文件只用于本地验证并保持 Git 忽略；synthetic fixture 可用于自动测试，但不会冒充真实数据。

实现使用 Python `openpyxl`，不依赖 Node/JS 生产运行时。当前未实现公式驱动的金融计算、图表或数据库导出；本文件是快照字段的可追溯导出，不是完整报告。

## 2026-09-26 本地 NVDA 验证

使用此前保存的八个本地输入离线重新生成了新的 schema 1.1 快照，并保留旧 schema 1.0 文件。随后使用 Python openpyxl 生成 Excel。快照为 NVDA、`saved_snapshot`，包含 100 根行情、87 份目标 filing、27281 条 fact 和 4 个来源；工作簿大小为 2,069,364 字节。Excel 位于 `.local_data/research/exports/NVDA-2026-09-18.xlsx`，未进入 Git。输入快照 SHA-256 为 `53ef46311e168e4f2ddec9be27717306b5dc95efb6e7b6c2253e91751e64759f`，Excel SHA-256 为 `872bdc782bc57bee437225900bca84ee5539275ae1d16164c20ce7a209e64a7a`。本轮网络请求为 0。未完成 Excel 客户端视觉验收；未实现图表。

## 2026-09-26 Excel 契约补充

`Market_Daily`、`SEC_Filings`、`SEC_Facts`、`Sources`、`Data_Quality` 和 `Run_Record` 均从第 4 行表头开启 AutoFilter，并冻结到 `A5`；Overview 保持简洁。Market_Daily 将 Date 与 Timestamp 分列，SEC_Facts 将 Filed At 与 Available At 分列，Run_Record 使用稳定字段映射并将嵌套值序列化为 JSON。

真实 NVDA Excel 已重新离线生成：100 根行情、87 份 filing、27281 条 fact、4 个来源。文件为 `.local_data/research/exports/NVDA-2026-09-18.xlsx`，大小 2,162,080 字节，SHA-256 为 `ca4e42727b406bca7b4ec3c58ee0114cdfc3f28b52e9b531d25b516784f4e902`。输入快照 SHA-256 仍为 `53ef46311e168e4f2ddec9be27717306b5dc95efb6e7b6c2253e91751e64759f`。网络请求为 0；尚未进行 Excel 客户端人工视觉验收；K 线图未实现。

## 2026-09-26 最终契约导出

最终导出文件为 `.local_data/research/exports/NVDA-2026-09-18.xlsx`，大小 2,162,042 字节，SHA-256 为 `21daafa6051e94eeadce9345bba7514334953baa71e2da2d74cb325e9496afb6`。输入快照 SHA-256 为 `53ef46311e168e4f2ddec9be27717306b5dc95efb6e7b6c2253e91751e64759f`。工作表数据行数为 Market 100、Filings 87、Facts 27281、Sources 4；AutoFilter 分别为 `A4:M104`、`A4:K91`、`A4:P27285`、`A4:J8`。前一次导出记录保留为早期导出。本次网络请求为 0，尚未进行 Excel 客户端人工视觉验收。
