# OpenBB 竞品证据

核验日期：2026-09-20。证据范围：OpenBB 官网、官方文档和官方 GitHub 仓库；未登录付费工作区、未安装、未调用数据 API，因此下文是官方资料核验，不是实测结果。

## 官方来源

- [OpenBB 官网文档](https://docs.openbb.co/)：介绍 Workspace、Open Data Platform（ODP）及其面向分析师、开发者和 AI 工作流的定位。
- [ODP Python 介绍](https://docs.openbb.co/odp/python)：说明统一 API 可通过 REST、Python、Jupyter、MCP、Docker、Workspace 和 Excel 使用，并列出扩展机制。
- [开发者指南](https://docs.openbb.co/platform/developer_guide)：说明 Core、Providers 和 Toolkits 的分层，以及可按需安装扩展。
- [OpenBB 官方 GitHub](https://github.com/OpenBB-finance/OpenBB)：仓库 README 说明 ODP、Workspace、AI Agent 接入方式，并显示仓库为 AGPLv3。
- [官方定价页](https://openbb.co/pricing/)：列出 Community、Lite、Pro 和 Snowflake 版本及公开价格信息。

## 能力核验表

| 维度 | 官方资料可确认内容 | 证据状态 |
| --- | --- | --- |
| 目标用户 | ODP 面向分析师、量化人员、开发者和 AI Agent；Community 价格页面向个人投资者，团队版面向协作团队。[来源](https://github.com/OpenBB-finance/OpenBB) [核验：2026-09-20] | 官方宣称 |
| 美股行情及延迟 | ODP 提供数据连接器和标准化数据模型；官方资料未给出统一的美股分钟延迟承诺，实际粒度取决于所接 Provider。[来源](https://docs.openbb.co/odp/python) [核验：2026-09-20] | 延迟未知 |
| 股票搜索 | ODP 示例和参考文档支持按资产类别查询；官方资料未证明 Workspace 提供与专门行情终端相同的搜索体验。[来源](https://docs.openbb.co/odp/python) [核验：2026-09-20] | 部分官方宣称，界面体验未知 |
| 自选股 | Workspace 文档介绍可组合的 dashboards 和 widgets；官方资料未明确个人自选股功能的完整规则。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 未知 |
| 价格、成交量及新闻告警 | 数据提供者和 widgets 可接入不同数据；统一的个人阈值告警、冷却和合并流程未在所查资料中明确。[来源](https://docs.openbb.co/odp/python/extensions) [核验：2026-09-20] | 数据接入官方宣称，告警未知 |
| 基本面和财务分析 | ODP 作为连接不同 Provider 和工具包的基础设施，可用于研究应用；具体覆盖取决于扩展和数据许可。[来源](https://docs.openbb.co/platform/developer_guide) [核验：2026-09-20] | 官方宣称，覆盖需逐 Provider 核验 |
| 新闻与情绪分析 | 官方仓库列出多类金融数据扩展的接入能力，但没有给出统一情绪模型或质量指标。[来源](https://github.com/OpenBB-finance/OpenBB) [核验：2026-09-20] | 未知 |
| 财报及公告问答 | Workspace 可把 PDF、图片、文本和表格作为资料，并支持接入 AI Agent；官方资料未证明对 SEC 财报提供固定问答产品和原文页码定位。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 资料接入官方宣称，财报问答未知 |
| 引用和原文定位 | widgets 含 source metadata；官方资料未承诺每个 AI 结论都有原始段落或页码引用。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 部分官方宣称，引用完整性未知 |
| AI 分析能力 | Workspace 官方资料支持集成自定义 AI Agent，并提供 Copilot 方案；未登录且未使用，不能写成实测。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 官方宣称，未实测 |
| 多 Agent 协作 | 官方资料支持接入“任何支持工作流的 AI agent”，但未证明内置固定的多 Agent 辩论、裁判和风控流程。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 接入能力官方宣称，内置多 Agent 未知 |
| 多空观点与风险审查 | 官方定价页的自定义 Agent 能力不等于已提供多空审查；具体流程未知。[来源](https://openbb.co/pricing/) [核验：2026-09-20] | 未知 |
| 每日收盘报告 | Workspace 支持 dashboards、apps 和导出，但所查官方资料未明确自动生成个人自选股收盘报告。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 未知 |
| 邮件或系统通知 | 官方资料提到分享、导出和协作，未明确个人邮件或系统告警通知。[来源](https://openbb.co/pricing/) [核验：2026-09-20] | 未知 |
| 历史报告 | 可保存 dashboards、notes 和 AI 生成 artifacts 的能力在 Workspace 文档中出现；历史报告版本与检索规则未明确。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 部分官方宣称，细节未知 |
| 历史判断复盘 | 所查官方资料未明确按 5/20 个交易日记录判断、评估归因和风险识别。[来源](https://docs.openbb.co/) [核验：2026-09-20] | 未知 |
| 数据可视化 | Workspace 以 widgets、charts、tables、PDF 和 images 作为展示层；ODP 可供研究 dashboard 使用。[来源](https://docs.openbb.co/workspace) [核验：2026-09-20] | 官方宣称 |
| 免费版本限制及价格 | Community 标为免费个人许可；Lite 页面列出每年 1,200 美元促销价/2,400 美元原价，Pro 为定制报价，Snowflake 为每席位每年 500 美元。Copilot 的 Community/Lite 细节和数据 Provider 成本仍需逐项核验。[来源](https://openbb.co/pricing/) [核验：2026-09-20] | 官方定价，未购买或实测 |

## 对 FinSight 的启发与边界

OpenBB 的强项是把多种数据源、Python/REST/MCP/Workspace 和可视化应用连接起来，适合作为数据接入或研究工作台的参考。FinSight 可以借鉴“Provider 与分析逻辑解耦、统一数据模型、可接入 Agent、widgets 展示”的设计思想，但不能把 OpenBB 的数据许可或 Workspace 商业功能直接当作本项目免费数据方案。

FinSight 需要独立实现并验证：面向美股个人投资者的现场搜索与自选股监测闭环、数据时间与来源显示、财报证据定位、多空反证和 Evidence Auditor、5/20 个交易日的多维复盘，以及与 Baseline A/B 对照的 Agent 评测。OpenBB 官方资料没有证明这些能力已按 FinSight 的定义组合起来。

## 未知与限制

- 未核验各 Provider 的实时/延迟、免费额度、历史长度、缓存和再分发许可。
- 未登录 Workspace 或 Copilot，未核验个人工作流的完整告警、通知和历史版本功能。
- 未做安装、API 调用、延迟、引用质量或模型输出测试；不存在 OpenBB 的实测指标。
- ODP 仓库为 AGPLv3，Workspace 和数据 Provider 还可能有单独条款；FinSight 采用前需做许可证与数据许可审查。
