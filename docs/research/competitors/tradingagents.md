# TradingAgents（TauricResearch）证据与差异分析

核验日期：2026-09-20。证据范围：TauricResearch 官方 GitHub 仓库及其 README、LICENSE、发布说明；未克隆、安装、配置模型或数据 API，因此所有能力描述均为仓库可见的官方资料，不是实测通过。

## 官方来源

- [官方 GitHub 仓库](https://github.com/TauricResearch/TradingAgents)：项目代码、README、目录和许可证入口。
- [官方 README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md)：角色、LangGraph、数据供应商、记忆、检查点、回测和免责声明。
- [官方 LICENSE](https://github.com/TauricResearch/TradingAgents/blob/main/LICENSE)：仓库标注 Apache-2.0。
- [官方 Releases](https://github.com/TauricResearch/TradingAgents/releases)：版本说明和变更记录。

## 系统架构

官方 README 将项目描述为模拟真实交易公司的多 Agent LLM 金融交易框架，并说明使用 LangGraph 组织图状流程。流程由分析师团队、研究团队、Trader、风险管理和 Portfolio Manager 组成；可配置研究深度、LLM、辩论轮数和数据供应商。[README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md) [核验：2026-09-20]

### Agent 角色

| 角色 | 官方资料描述 | 证据状态 |
| --- | --- | --- |
| Fundamentals Analyst | 评估公司财务和表现指标，识别内在价值和风险信号。 | 官方仓库可见，未实测 |
| Sentiment Analyst | 汇总新闻标题、StockTwits 和 Reddit 讨论，形成情绪判断。 | 官方仓库可见，未实测 |
| News Analyst | 监测全球新闻和宏观指标并解释影响。 | 官方仓库可见，未实测 |
| Technical Analyst | 使用 MACD、RSI 等技术指标研究价格模式。 | 官方仓库可见，未实测 |
| Bullish / Bearish Researchers | 对分析师结果进行多空研究和结构化辩论。 | 官方仓库可见，未实测 |
| Trader | 汇总研究并提出交易时机和规模。 | 官方仓库可见，未实测 |
| Risk Management | 根据波动率、流动性等因素评估风险并调整策略建议。 | 官方仓库可见，未实测 |
| Portfolio Manager | 审批或拒绝交易提案；官方 README 称获批后发送到模拟交易所执行。 | 模拟交易流程官方宣称，未实测 |

## 工作流程、数据和状态

1. 用户选择股票、日期、模型和研究深度，图流程调用分析师。
2. 分析师输出基本面、技术、新闻和情绪观点。
3. 多空研究员进行讨论，Trader 汇总，风险管理审查，Portfolio Manager 作最终决定。
4. 官方 README 说明市场覆盖使用 Yahoo Finance 能覆盖的代码格式；可配置 yfinance、SEC EDGAR、Alpha Vantage、FRED 等供应商，具体是否可用取决于配置和密钥。[README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md) [核验：2026-09-20]
5. README 说明决策日志保存到本地 Markdown，后续运行会读取同一股票的近期判断和实现收益反思；可选 LangGraph checkpoint 以 SQLite 保存中断恢复状态。[README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md) [核验：2026-09-20]
6. 官方 README 说明 `run_backtest` 会在股票和日期网格上运行流程，并按持有窗口和相对基准汇总结果；这属于框架提供的评估入口，不是本项目已验证的效果指标。[README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md) [核验：2026-09-20]

## 与指定维度对应的核验

| 维度 | 官方资料可确认内容 | 证据状态 |
| --- | --- | --- |
| 目标用户 | 面向金融交易研究和多 Agent 实验；官方免责声明称研究用途，不是投资、金融或交易建议。 | 官方宣称 |
| 美股行情及延迟 | 可用 Yahoo Finance 覆盖的代码格式，并可选择在线工具或缓存/供应商；没有统一分钟延迟承诺。 | 延迟未知 |
| 股票搜索 | CLI 允许选择 ticker；搜索体验和公司名称解析的完整范围未独立说明。 | 部分官方宣称 |
| 自选股 | 支持一次运行选择 ticker 和传入 portfolio context；不是 FinSight 定义的用户长期自选股管理。 | 部分官方宣称，产品形态未知 |
| 价格、成交量及新闻告警 | 分析流程会使用价格、技术、新闻和情绪数据；分钟监测、阈值告警和通知未说明。 | 告警未知 |
| 基本面和财务分析 | Fundamentals Analyst；README 还说明可用 SEC EDGAR 的按申报时间点数据。 | 官方宣称，未实测 |
| 新闻与情绪分析 | News Analyst、Sentiment Analyst，来源包括新闻标题、StockTwits 和 Reddit。 | 官方宣称，未实测 |
| 财报及公告问答 | SEC EDGAR 基本面可用于日期敏感的分析；没有通用财报自然语言问答界面的证据。 | 部分官方宣称，问答未知 |
| 引用和原文定位 | README 说明数据时间点和供应商，但未承诺每个结论显示文件、段落或页码引用。 | 未知 |
| AI 分析能力 | 多个 LLM Agent、可配置模型和结构化决定流程在仓库中描述。 | 官方宣称，未实测 |
| 多 Agent 协作 | 分析师、研究员、Trader、风控和 Portfolio Manager 组成 LangGraph 流程。 | 官方仓库可见，未实测 |
| 多空观点与风险审查 | Bullish/Bearish Researchers 讨论，Risk Management 审查，Portfolio Manager 作决定。 | 官方仓库可见，未实测 |
| 每日收盘报告 | README 有保存分析报告/决策记录的描述，但没有 FinSight 式自选股收盘日报调度证据。 | 部分官方宣称，日报未知 |
| 邮件或系统通知 | 未见官方 README 对邮件或系统消息投递的说明。 | 未知 |
| 历史报告 | 报告/决策日志会保存到本地路径；完整报告检索、版本和用户界面未知。 | 部分官方宣称 |
| 历史判断复盘 | 决策日志可生成反思，`backtest` 可按日期网格评分；并非 FinSight 预设的 5/20 交易日多维复盘。 | 官方宣称，口径不同 |
| 数据可视化 | CLI 显示分析过程和结果；README 未证明有 FinSight 计划的 K 线、财务、情绪和行业组合仪表板。 | 部分官方宣称，范围未知 |
| 免费版本限制及价格 | GitHub 仓库公开、Apache-2.0；运行需要自行配置 LLM/数据供应商，模型和 API 费用不由仓库统一定价。 | 许可证明确，运行成本未知 |

## RAG、记忆、监控、评测和真实交易边界

- **RAG**：README 明确出现 BM25 记忆检索的版本变更，但没有证据表明它实现了“财报/公告解析 → BM25 + Embedding → RRF → reranker → 引用核验”的金融 RAG 链路。FinSight 不应把 TradingAgents 的记忆检索直接等同于金融 RAG。
- **记忆**：有本地决策日志、同 ticker 历史反思和可选 checkpoint；这是可借鉴的状态持久化思路。[README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md) [核验：2026-09-20]
- **监控**：仓库有运行日志、进度显示和错误恢复相关代码/发布说明；未见面向生产的 Token、P50/P95、数据源可用率和告警成功率面板定义。应标为未知。
- **评测**：官方提供 backtest 和结果汇总入口，但未提供 FinSight 所需的 RAG Recall@K、引用准确率、归因准确率、风险识别率或真实用户指标，也没有在本次研究中运行它。[README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md) [核验：2026-09-20]
- **真实交易**：README 描述的是模拟交易所；未发现连接真实券商并执行真实订单的证据。FinSight 的“不连接真实券商、不执行真实交易”边界仍需独立保持。

## 许可证、可借鉴内容与必须独立的部分

仓库根目录显示 Apache-2.0，代码复用仍需保留许可和版权声明，并逐项检查依赖许可证。[LICENSE](https://github.com/TauricResearch/TradingAgents/blob/main/LICENSE) [核验：2026-09-20]

FinSight 可以在概念层借鉴：按专业角色拆分任务、用 LangGraph/状态机表达协作、设置多空辩论和风控门、保存决策日志、使用日期网格做回测，以及把数据供应商抽象成可替换层。借鉴不等于复制仓库代码或其提示词。

FinSight 必须独立实现并用自己的数据和评测证明：来源可点击且可定位到原文、Point-in-Time 过滤、Evidence Auditor、金融 RAG 的检索与引用核验、分钟级自选股告警合并、系统/邮件日报、5/20 个交易日的事实/事件/归因/风险/方向复盘、LLMOps 监控，以及面向个人投资者的简洁摘要和展开详情。TradingAgents 的多 Agent 角色本身不能作为 FinSight 的差异化成果。

## 未知与未实测

- 未安装、未调用任何 LLM 或金融 API，不能报告延迟、成功率、准确率、费用或收益。
- 数据供应商的当前免费额度、许可、缓存和再分发范围需逐项核验。
- 日报、邮件、系统告警、原文页码引用、用户自选股管理和生产监控的实现范围未知。
- GitHub 页面会随版本更新；本文记录的是 2026-09-20 可见资料，后续应在功能或版本变化时重新核验。
