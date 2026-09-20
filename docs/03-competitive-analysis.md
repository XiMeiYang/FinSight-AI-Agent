# 竞品分析

状态：截至 2026-09-20，已完成基于官方公开资料的案头调研。未注册付费账号、未绕过付费墙、未安装或调用竞品 API，因此本文不包含实测延迟、实测成功率、用户调研结论或产品效果指标。每份证据文件记录官方链接和核验日期；“官方宣称”表示资料中的产品说明，不等于本项目实测。

## 调研范围与证据标准

本轮核验 Yahoo Finance、TradingView、FinChat、Koyfin、OpenBB 和 TauricResearch/TradingAgents。Koyfin 之所以作为第四个产品，是因为本轮官方帮助、功能和定价页面对 watchlist、alerts、新闻/公告/财报和通知渠道的公开说明更完整；这只是资料可核验性选择，不是总体产品排名。

证据优先级为官网功能页、官方帮助文档、官方定价页和官方 GitHub。每条结论都在相应证据文件中附官方链接与“核验：2026-09-20”。没有查到的能力写“未知”；没有登录、购买或运行的内容写“未实测”，不把未知写成“不支持”。

详细记录：

- [Yahoo Finance 证据](research/competitors/yahoo-finance.md)
- [TradingView 证据](research/competitors/tradingview.md)
- [FinChat 证据](research/competitors/finchat.md)
- [Koyfin 证据](research/competitors/koyfin.md)
- [OpenBB 证据](research/competitors/openbb.md)
- [TradingAgents 深入证据](research/competitors/tradingagents.md)

模拟访谈 [simulated-interview-001.md](research/simulated-interview-001.md) 只是设计参考：它没有经过真实招募、录音、计时或独立编码，不能作为需求已验证或竞品结论的证据。

## 能力矩阵

矩阵只给出官方资料可核验的范围。具体链接、套餐、版本和限制请打开每个产品的证据文件；“部分/未知”表示官方资料不足，不能据此断言没有该能力。

### 研究、数据与告警

| 产品 | 目标用户 | 美股行情/延迟 | 搜索与自选股 | 价格/成交量/新闻告警 | 基本面、新闻与可视化 |
| --- | --- | --- | --- | --- | --- |
| [Yahoo Finance](research/competitors/yahoo-finance.md) | 个人投资者和市场信息使用者（官方定位）；细分用户效果未知 | 提供市场数据；不同市场和套餐的实时/延迟规则需按官方说明核验，统一延迟未知 | 搜索、watchlist 和行情页面为官方功能；完整规则以证据页为准 | 价格/新闻等提醒有官方说明；成交量、冷却和合并细节部分未知 | 价格、基本面、新闻和图表可见；AI/情绪和财报证据定位有限或未知 |
| [TradingView](research/competitors/tradingview.md) | 交易者、投资者和图表研究用户（官方定位） | 覆盖多市场；部分实时数据需交易所数据订阅，免费/实时差异和具体延迟以官方页为准 | Symbol search、watchlist、图表和 screener 为官方功能 | 价格、技术和条件告警是官方功能；新闻/成交量告警组合、通知限额需按套餐核验 | 图表和技术分析很强；基本面、新闻情绪、财报问答和引用链未按 FinSight 口径确认 |
| [FinChat](research/competitors/finchat.md) | 面向投资研究的 AI 用户（官方定位） | 依赖其披露的数据和产品计划；分钟延迟、数据刷新和免费边界未知 | 公司/股票查询和研究问答为官方宣称；长期 watchlist 与阈值监测部分未知 | 价格异动、成交量、新闻告警和通知组合未知 | AI 问答、公司与财务研究为官方宣称；引用、新闻情绪、原文定位需逐项核验 |
| [Koyfin](research/competitors/koyfin.md) | 个人投资者、研究人员和顾问团队（官方定价/功能定位） | 全球股票、财务和估值数据；统一行情延迟承诺及数据许可未知 | watchlists、portfolios 和搜索/分析页面为官方宣称 | price、technical、valuation、news、press release、filing、transcript alerts，支持桌面、邮件和移动通知；限额随套餐变化 | 财务报表、估值、新闻、公告、transcript、图表和 dashboard 为官方宣称；逐条引用和 AI 结论核验未知 |
| [OpenBB](research/competitors/openbb.md) | 分析师、量化人员、开发者和 AI Agent；Community 面向个人 | 由 Provider 决定，无统一美股分钟延迟承诺 | ODP 查询和 Workspace widgets 可组合；个人自选股产品形态未知 | 数据接入可扩展；个人阈值告警、冷却和通知未知 | Provider、toolkit、widgets、dashboard 和 AI Agent 接入为官方宣称；引用完整性未知 |
| [TradingAgents](research/competitors/tradingagents.md) | 多 Agent 金融交易研究和实验用户 | 可用 Yahoo Finance 覆盖的 ticker 和其他供应商；统一延迟未知 | CLI 选择 ticker；长期自选股管理未知 | 使用价格、技术、新闻和情绪数据；分钟告警和通知未知 | 专业 Agent 与结果展示为官方仓库描述；不是成熟的个人行情终端，引用和可视化范围未知 |

### AI、证据、报告与复盘

| 产品 | 财报/公告问答与原文引用 | AI/多 Agent/多空/风控 | 日报、历史报告、判断复盘 | 免费版本与价格核验 |
| --- | --- | --- | --- | --- |
| Yahoo Finance | 财务和新闻内容可查；逐段引用、页码和 RAG 问答未知 | AI 能力、内置多 Agent 和多空风控未知 | watchlist/portfolio 历史访问有部分说明；自动收盘报告和 5/20 日复盘未知 | 按官方定价/服务地区核验；不能用本轮资料推断所有功能均免费 |
| TradingView | 财报/公告原文问答和引用未知 | 技术图表与社区脚本为主要能力；内置多 Agent、裁判和风险证据审查未知 | 图表、布局和提醒可保存；自动收盘报告与历史判断复盘未知 | 免费层和付费层、数据订阅及告警限额以官方价格页为准；未购买 |
| FinChat | AI 财务问答和公司资料可能包含引用；原文位置完整性未知 | AI 研究为官方宣称；多 Agent、多空交叉和独立证据审计未知 | 报告、workspace、通知和长期复盘组合未知 | 免费试用/套餐和额度以官方定价页为准；未登录或付费 |
| Koyfin | filings、transcripts、news 可查，原文定位和 AI 引用完整性未知 | 数据研究和 dashboards 强；内置多 Agent、辩论和裁判未知 | reports、dashboards 和 portfolio history 有部分官方说明；5/20 日判断复盘未知 | Free $0、Plus $39/月、Premium $79/月及 Advisor 计划等公开价格，具体功能限额见证据文件；未购买 |
| OpenBB | 可接入文件和 AI Agent，固定 SEC 问答及段落引用未知 | 可接入自定义 Agent；内置多 Agent、辩论和风控未知 | dashboard/notes/artifacts 可保存；自动日报和 5/20 日复盘未知 | Community 标为免费个人许可；Lite/Pro/Snowflake 价格见官方页；未登录 |
| TradingAgents | SEC EDGAR 等日期敏感数据可用于分析；没有通用财报问答和逐段引用证据 | LangGraph 多 Agent、分析师、多空研究员、Trader、风控和 Portfolio Manager 为官方仓库描述 | 决策日志、反思、checkpoint 和 backtest 为官方仓库描述；不是 FinSight 的 5/20 多维复盘 | Apache-2.0；运行需自备模型/数据供应商，费用未知；未安装 |

## TradingAgents 深入分析

### 可以借鉴的设计

TradingAgents 展示了按专业角色拆分研究、用状态图连接角色、加入多空讨论和风控门、保存决策日志、支持 checkpoint 以及用日期网格回测的思路。这些是架构层参考；FinSight 不复制其仓库代码、提示词、界面或结果，也不把其公开 backtest 入口当作效果证明。

### FinSight 必须独立实现的差异化

FinSight 的差异化应围绕产品闭环而不是 Agent 数量：

1. 每个重要结论展示数据时间、来源和可点击原文位置，并由 Evidence Auditor 检查数字和时间顺序。
2. 财报与公告走明确的 Point-in-Time RAG 流程，区分文档公开时间、事件时间、抓取时间和数据版本。
3. 面向美股个人投资者提供现场搜索、自选股分钟级异动、告警冷却/合并、收盘简报和系统/邮件投递。
4. 保存当时可见的数据和判断，在 5、20 个交易日后分别评估事实、事件、归因、风险和方向，不只看股票涨跌。
5. 用 Baseline A（人工收集）和 Baseline B（单次大模型）比较引用、归因、风险和成本，公开真实运行结果。

TradingAgents 的研究用途、模拟交易边界和 Apache-2.0 许可不能替代 FinSight 自己的安全边界；FinSight 仍不连接真实券商、不执行真实交易、不承诺收益。

## 竞品已较好解决的问题

基于官方资料，可以确认这些问题已有成熟产品能力覆盖或明确产品化方向：行情与公司搜索、watchlist、图表和技术指标、基本面/估值表格、新闻/公告/财报聚合、阈值告警、桌面/邮件/移动通知，以及多数据源接入和可组合 dashboard。覆盖深度、实时性和套餐限制仍取决于供应商和方案，不能用矩阵替代实测。

## 仍未被完整解决或尚不清楚的问题

从公开官方资料的交集看，以下组合能力仍缺乏可核验的统一闭环：对每个结论做原文级引用核验；严格按 Point-in-Time 防未来泄漏；把新闻时间与价格变化做因果顺序检查；让多空观点共享证据并由独立风控/裁判审查；将异动、日报和历史判断复盘连接起来；同时公开 Agent 的引用、归因、风险、延迟和成本评测。这里的“缺乏可核验”不是断言竞品一定没有，而是本轮官方资料未明确证明。

## FinSight 的可能方向与低价值重复建设

可能成立的方向是“有证据的个人投研闭环”：用现成行情、图表、筛选和通知能力，集中建设可溯源金融 RAG、时间一致性、多空反证、风险审计和 5/20 日复盘，再用真实评测证明何时有帮助。多 Agent 角色数量、普通 K 线、通用 watchlist、基础价格告警、又做一个通用 dashboard，单独看容易重复造轮子，MVP 应先验证证据链和复盘价值。

## 结论边界和后续验证

本报告是官方资料研究，不是用户需求验证，也没有证明 FinSight 优于任何竞品。下一步应只做一个动作：选择一条最小的真实研究任务，按同一股票、同一截止时间和同一问题，把 FinSight 设计稿与一个可公开使用的竞品流程做可复现的人工走查，记录来源、耗时、缺口和未知项；在完成用户验证与 API 许可核验前，不冻结技术栈或性能指标。
