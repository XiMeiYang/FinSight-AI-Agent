# TradingView 竞品证据卡

> 调研状态：已完成官方资料核验，未注册付费账号，未购买额外交易所实时行情，未连接券商，未调用 TradingView API。
>
> 核验日期：2026-09-20（Asia/Shanghai）。
>
> 证据口径：本文只使用 TradingView 官网、官方 Help Center、官方定价页和官方市场数据覆盖页。带“官方宣称（未实测）”的内容来自公开页面；没有找到明确证据的内容标为“未知”，不会把未发现写成“不支持”。本文不是用户需求验证，也不是对付费套餐或实时行情的实测报告。

## 产品定位与证据边界

TradingView 官方定价页将产品定位为覆盖不同层级交易/投资需求的市场分析平台，并展示图表、技术分析、筛选器、watchlists、组合、提醒、回放、脚本和移动/桌面应用。官方 Features 页强调跨市场图表、基本面、筛选器、告警和经济/财报日历。定价页写有“100 million traders”等宣传语；本文只把它当作官方定位文案，不把它当作独立市场规模验证。

- [TradingView pricing](https://www.tradingview.com/pricing/)（官方定价页；核验日期：2026-09-20）
- [TradingView features](https://www.tradingview.com/features/)（官方产品页；核验日期：2026-09-20）

TradingView 的行情是否实时取决于数据源、市场和是否购买直接交易所数据。免费计划、订阅计划和市场数据订阅是不同概念，不能把“订阅 TradingView”直接等同于所有美国交易所实时行情。

## 统一能力矩阵

| 维度 | 官方证据与当前结论 | 状态 |
| --- | --- | --- |
| 目标用户 | 官方提供 Basic 免费计划及 Essential/Plus/Premium/Ultimate 多层计划，覆盖图表、技术分析、筛选、提醒、回放和交易连接；产品页面向交易者和投资者描述市场分析能力。 | 官方宣称；未实测 |
| 美股行情及延迟情况 | 官方 Help 称美国股票默认图表使用 Cboe 实时数据，免费使用但与 NYSE/Nasdaq 主市场可能有细微差异，低时间框架或低流动性标的更明显；直接 NASDAQ、NYSE、NYSE Arca 实时数据需单独购买。官方数据覆盖页列出各交易所的免费延迟/实时价格。 | 官方宣称；未购买/未实测 |
| 股票搜索 | 官方 watchlist 文档说明可通过 symbol search 添加证券；Features 页提供 global command search；Stock Screener 可按证券信息、市场数据、财务和技术字段筛选。 | 官方宣称；未实测 |
| 自选股 | Watchlists 支持创建、重命名、分组、导入、排序、复制、删除和自定义列表；官方定价页列出 Basic 1 个 watchlist/30 个 symbol，付费计划每个列表最多 1,000 个 symbol（套餐总列表数和其他限制不同）。 | 官方宣称；未实测 |
| 价格、成交量及新闻告警 | 官方支持价格、技术指标、策略、绘图对象和 watchlist alerts；条件、触发频率、到期时间和消息可配置。Watchlist alerts 可对列表内多个 symbol 分别触发；官方热榜支持成交量、涨跌幅、区间、跳空等市场异动筛选。 | 官方宣称；未实测 |
| 基本面和财务分析 | 官方 Stock Screener 提供财务报表、估值、增长、利润率、风险等 500+ 基本面/技术字段的产品说明；Help 说明可查看损益表、资产负债表和现金流。官方还说明金融数据来自年度/中期公司报告并经过标准化，标准化数值可能不同于公司原始报告。 | 官方宣称；未实测 |
| 新闻与情绪分析 | Watchlist 可聚合列表中标的新闻，symbol details 提供 flash news；官方社区页面描述用户观点、Ideas 和 Minds，帮助用户了解不同市场观点。官方情绪指标文档本次找到的是加密货币社交媒体 sentiment%，没有找到美股新闻自动情绪分数的明确说明。 | 新闻聚合/社区观点：官方宣称；美股自动新闻情绪：未知；未实测 |
| 财报及公告问答 | 官方支持财务报表、earnings、估计、surprise、财报日历和公司报告字段；没有在公开官方资料中找到类似财报原文的自然语言问答或 10-K/8-K 对话式问答说明。 | 财报数据/日历：官方宣称；财报/公告问答：未知；未实测 |
| 引用和原文定位 | 官方说明财务数据的主来源是年度和中期公司报告，并会按标准化方法调整；Earnings 文档区分公司新闻稿中的 As reported 与 Standardized。公开帮助文档没有承诺回答为每个金融数字提供原始文件页码、段落或可审计证据链。 | 来源说明：官方宣称；逐结论原文定位：未知；未实测 |
| AI 分析能力 | AI Screener 官方帮助页称可用自然语言把筛选意图转成筛选器、列和排序，并提供 explanation；当前说明为 public beta、只在 Stock Screener、仅付费用户，移动端暂不支持，额度按套餐而变。 | 官方宣称；未实测 |
| 多 Agent 协作 | 官方资料核验范围内未找到多个 LLM Agent 角色、任务路由、协作状态机或裁判机制的产品说明。 | 未知 |
| 多空观点与风险审查 | TradingView 社区支持用户分享多种观点、Ideas 和讨论，官方帮助页提到通过不同观点减少偏见；这不等同于系统自动生成多头/空头两方证据辩论或独立风控审查。后两者在公开资料中未知。 | 社区观点：官方宣称；系统多空/风控：未知；未实测 |
| 每日收盘报告 | 官方有 earnings/economic calendars、watchlist news 和组合/列表概览；未找到按用户自选股在收盘后自动生成结构化多维研究报告的官方说明。 | 未知 |
| 邮件或系统通知 | Alerts 可发送 App notification、桌面弹窗、邮件、声音和 webhook；官方帮助还支持 watchlist alert 和频率设置。Webhook 要求安全端点、2FA，并可能发生投递失败；官方资料未证明其提供 FinSight 所需的每日收盘报告邮件。 | 告警通知：官方宣称；收盘报告邮件：未知；未实测 |
| 历史报告 | 官方支持历史图表、Bar Replay、策略测试、导出和保存 chart layouts；定价页列出按套餐的历史 bar 数、分钟/秒/逐笔历史和回放。Replay Trading 帮助页明确说明交易数据只在当前 session 中可见、不会保存。用户生成的研究报告历史归档未知。 | 历史行情/回放：官方宣称；历史研究报告：未知；未实测 |
| 历史判断复盘 | Bar Replay 可回看历史价格并模拟交易；官方帮助未说明保存一次研究判断、冻结 Point-in-Time 证据并在 5/20 个交易日后自动评价事实、归因、风险和方向。 | 回放：官方宣称；5/20 日判断复盘：未知 |
| 数据可视化 | 官方 Features 和定价页列出多图布局、17/21 类图表、指标、Volume Profile、Volume Footprint、Fundamental Graphs、经济/财报日历、热图和筛选器；具体能力受套餐、数据源和市场影响。 | 官方宣称；未实测 |
| 免费版本限制及价格 | 官方定价页显示 Basic $0 forever、无信用卡要求；页面当前展示 Essential $12.95/月、Plus $29.95/月、Premium $59.95/月（均按年计费的页面价格）和 Ultimate $199.95/月（按年计费），并列出每档图表、历史 bar、watchlist、告警、筛选和 AI Screener 请求额度。美国主要交易所直接实时数据另收费，非专业用户价格以官方数据页为准。 | 官方宣称；未购买/未实测 |

## 重点证据整理

### 美国行情与交易所数据

TradingView 官方帮助把“产品订阅”和“交易所数据订阅”区分开来。美国股票图表默认使用 Cboe 数据，官方称这类数据实时且无每用户交易所费用，但与主交易所的价格更新、低时间框架和低流动性标的可能存在差异。若需要直接的 NASDAQ、NYSE 或 NYSE Arca 数据，需要额外购买相应市场数据；官方市场覆盖页列出不同市场的免费延迟、非专业和专业价格。

- [Is US stock market data free by default?](https://www.tradingview.com/support/solutions/43000473924-is-us-stock-market-data-free-by-default/)（官方 Help；核验日期：2026-09-20）
- [How to purchase additional market data](https://www.tradingview.com/support/solutions/43000471705-how-to-purchase-additional-market-data/)（官方 Help；核验日期：2026-09-20）
- [TradingView market data coverage](https://www.tradingview.com/data-coverage/)（官方数据页；核验日期：2026-09-20）

因此，FinSight 若以 TradingView 的公开产品体验作竞品参照，应记录具体数据源、交易所、时间粒度和是否直接主市场数据，不能只写“TradingView 实时”。本次没有购买行情，也没有实测具体 ticker 的更新间隔。

### 搜索、自选股、图表与筛选

官方 watchlist 帮助说明，用户可以通过 symbol search 添加标的，创建多个列表、分组、导入 txt、查看价格/成交量/扩展时段变化、基本面和新闻。Advanced view 可以按证券类型、行业、交易所或自定义分组，并查看财务、表现、风险、技术、财报和股息数据。定价页给出 Basic 只有 1 个 watchlist、30 个 symbol；Essential 及以上页面显示每个列表最多 1,000 个 symbol，但其他数量和告警限制按套餐区分。

- [Mastering TradingView watchlists](https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/)（官方 Help；核验日期：2026-09-20）
- [Watchlist advanced view mode](https://www.tradingview.com/support/solutions/43000771546-watchlist-advanced-view-mode/)（官方 Help；核验日期：2026-09-20）
- [TradingView pricing](https://www.tradingview.com/pricing/)（官方定价页；核验日期：2026-09-20）

Stock Screener 进一步提供证券信息、市场数据、技术指标、财务报表、股息、估值、增长、利润率和杠杆等筛选字段；官方页称覆盖 150+ 交易所、50+ 国家和 500+ 基本面/技术字段，但本次未登录核验各地区字段可见性。

- [TradingView Stock Screener](https://www.tradingview.com/support/solutions/43000718866-tradingview-stock-screener-trade-smarter-not-harder/)（官方 Help；核验日期：2026-09-20）

### 告警、通知和异动

官方告警帮助页支持价格和技术条件、指标、策略、绘图对象以及 watchlist。可配置触发频率（例如一次、每次、每根 bar 收盘或每分钟）、到期日期、消息和占位符。通知渠道包括 App、弹窗、邮件、声音和 webhook；webhook 要求 2FA，官方提醒不要在请求体中放密码等敏感信息，也说明远端超过三秒或偶发网络问题可能导致投递失败。

- [Introduction to TradingView alerts](https://www.tradingview.com/support/solutions/43000520149-introduction-to-tradingview-alerts/)（官方 Help；核验日期：2026-09-20）
- [How to set up alerts](https://www.tradingview.com/support/solutions/43000595315-how-to-set-up-alerts/)（官方 Help；核验日期：2026-09-20）
- [Watchlist alerts](https://www.tradingview.com/support/solutions/43000739708-watchlist-alerts-your-trading-edge/)（官方 Help；核验日期：2026-09-20）
- [How to configure alerts](https://www.tradingview.com/support/solutions/43000763312-learn-how-to-configure-alerts/)（官方 Help；核验日期：2026-09-20）
- [Webhook alerts](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/)（官方 Help；核验日期：2026-09-20）

官方 Hotlists 页面还列出 volume gainers、percent change gainers/losers、percent range、gap 等动态列表。它能帮助识别市场异动，但公开资料未说明会自动结合公司新闻、行业和宏观证据解释异动原因，也未说明 FinSight 所需的告警冷却/事件合并策略。

- [TradingView hotlists](https://www.tradingview.com/support/solutions/43000762029-discover-market-movers-with-tradingview-hotlists/)（官方 Help；核验日期：2026-09-20）

### 财务数据、新闻、社区与引用

TradingView 官方财务帮助文档说明可从公司市场页或 Stock Screener 查看损益表、资产负债表和现金流。官方还解释其数据基于年度和中期公司报告，由数据提供商按标准化方法处理，因此标准化数字可能与公司原始报告不同；Earnings 文档区分 company press release 的 As reported、标准化 GAAP EPS、估计和 surprise。

- [How to read financial statements](https://www.tradingview.com/support/solutions/43000760059-how-to-read-financial-statements/)（官方 Help；核验日期：2026-09-20）
- [Why financial data differs from other sources](https://www.tradingview.com/support/solutions/43000540145-why-does-financial-data-differ-from-other-sources/)（官方 Help；核验日期：2026-09-20）
- [Earnings](https://www.tradingview.com/support/solutions/43000629790-earnings/)（官方 Help；核验日期：2026-09-20）

Watchlist 的 Advanced view 有 News 页面，symbol details 有 flash news，官方也有社区 Ideas 和 Minds。官方对加密货币提供社交媒体 sentiment% 的单独说明，但本次没有找到美股新闻的自动情绪评分、新闻到价格的时间因果判断或公告原文问答文档。不能把社区观点数量或热度当作经过校准的新闻情绪。

- [Filter news by watchlist](https://www.tradingview.com/support/solutions/43000734013-filter-by-watchlist/)（官方 Help；核验日期：2026-09-20）
- [TradingView social network](https://www.tradingview.com/support/solutions/43000761245-tradingview-social-network/)（官方 Help；核验日期：2026-09-20）
- [Sentiment %](https://www.tradingview.com/support/solutions/43000739593-sentiment/)（官方 Help；核验日期：2026-09-20；该页面针对加密货币社交媒体情绪）

### AI Screener

官方 AI Screener Help 页把功能描述为：用户用自然语言表达筛选想法，系统匹配筛选器、列和排序，并提供解释。官方同时注明它处于 public beta，只在 Stock Screener，当前面向付费用户，额度取决于套餐且可能变化，移动端暂不支持。本次未注册付费账号，也没有把自然语言请求提交给该功能，因此只记录为官方宣称，不能写成实测可用或质量结论。

- [How to use the AI Screener](https://www.tradingview.com/support/solutions/43000785770-how-to-use-the-ai-screener/)（官方 Help；核验日期：2026-09-20）

官方资料没有说明 AI Screener 是否读取财报原文、是否生成研究报告、是否引用证据、是否做多空辩论、是否使用多个 Agent 或是否具备金融风险审查。上述项目能力均应记为未知。

### 历史数据、回放和复盘边界

官方 Supercharts/Bar Replay 文档支持回看历史市场行为、练习交易和策略测试；定价页按套餐列出分钟、秒和 tick 历史数据范围以及 Bar Replay。Replay Trading 页面明确写出交易数据和结果只在当前 session 中可见、不会保存。它与 FinSight 需要的“保存一次自然语言判断、证据快照、数据截止时间，并在 5/20 个交易日后复盘判断质量”是不同能力，后者在官方资料中未知。

- [Getting started with Supercharts](https://www.tradingview.com/support/solutions/43000746464-getting-started-with-supercharts/)（官方 Help；核验日期：2026-09-20）
- [Learn to trade on historical data](https://www.tradingview.com/support/solutions/43000691889-learn-to-trade-on-historical-data/)（官方 Help；核验日期：2026-09-20）
- [TradingView pricing](https://www.tradingview.com/pricing/)（官方定价页；核验日期：2026-09-20）

## 对 FinSight 的可比启示

### 已被 TradingView 官方产品覆盖的方向

- 搜索、watchlist、分组、导入、K 线、技术指标、策略回放、筛选器、财务字段、财报/经济日历、新闻聚合和多渠道告警已经是成熟能力。
- TradingView 具备很强的图表、技术分析、跨市场覆盖和可编程 Pine Script 生态。FinSight 不应把“有 K 线/成交量/技术指标”作为主要差异化。
- AI Screener 已将自然语言映射到筛选条件并解释筛选结果，FinSight 的自然语言意图识别需要进一步连接数据证据、计算、引用和审计，不能只重复自然语言筛选。
- 免费计划与付费套餐有明确的告警、历史数据、watchlist、图表和筛选额度，额外实时交易所数据也有独立费用；这为 FinSight 设计低成本、允许 5–15 分钟延迟的 MVP 提供了现实参照，但不代表 FinSight 可以复用 TradingView 数据或许可。

### 仍需用证据核验、不能预先宣称空白的方向

- 逐数字原始文件定位、引用完整性、截止时间过滤和 Point-in-Time 快照：TradingView 公开说明了财务数据来源和标准化，但没有公开 FinSight 所需的完整证据链格式。
- 多 Agent 角色路由、多空证据辩论、Evidence Auditor、风险阻断和裁判：官方资料未披露，仍应写“未知”。
- 按自选股在收盘后生成可展开的完整研究报告、保存历史报告和自动 5/20 个交易日复盘：官方有 watchlist、新闻、日历、回放和交易报告，但完整研究闭环未知。
- 对新闻进行时间顺序检查、替代解释和历史相似事件验证：官方资料没有给出明确信息。

### 需要避免重复造轮子的方向

如果 FinSight 只提供 K 线、指标、筛选器、watchlist、价格/技术告警、财务字段、新闻列表、回放和自然语言筛选，功能上会与 TradingView 高度重叠。更有区分度的候选应是“证据驱动的研究工作流”：围绕 SEC/公司原文建立可定位 RAG，保存当时可见数据，区分事实/计算/判断，组织多空反证与风险审核，并在 5/20 个交易日后评价判断质量。这些是设计方向，仍需真实实现和评测才能证明成立。

## 未知项与后续核验清单

以下内容在本次官方公开资料核验中没有足够证据，统一保留为未知或未实测：

1. 不同美国 ticker、Cboe 与主交易所之间的实际价格更新差异、刷新间隔、盘前/盘后覆盖和套餐限额。
2. 各套餐在不同地区的完整基础行情、分钟/秒/tick 历史长度、AI Screener 月度请求和告警额度；定价页内容可能调整。
3. AI Screener 的模型、提示处理、错误率、稳定性、引用能力和可复现性。
4. 美股新闻情绪分数、新闻事件到价格的自动归因、公告/财报自然语言问答和原文定位。
5. 多 Agent 协作、任务路由、多空辩论、风控审查、裁判和 LLMOps 监控。
6. 用户研究报告保存、报告版本、判断登记、Point-in-Time 数据快照和 5/20 个交易日复盘。
7. 具体数据供应商、再分发、缓存、导出和项目展示许可；官方财务来源说明不等于允许 FinSight 复用其数据。
8. 告警投递的真实成功率、冷却/合并策略、webhook 重试和用户取消订阅流程。

## 来源清单

| 官方来源 | 用途 | 核验日期 |
| --- | --- | --- |
| [TradingView pricing](https://www.tradingview.com/pricing/) | 免费/付费计划、额度、历史和告警 | 2026-09-20 |
| [TradingView features](https://www.tradingview.com/features/) | 图表、告警、筛选、财报日历、市场工具 | 2026-09-20 |
| [US stock market data free by default](https://www.tradingview.com/support/solutions/43000473924-is-us-stock-market-data-free-by-default/) | Cboe 默认实时数据及差异 | 2026-09-20 |
| [Purchase additional market data](https://www.tradingview.com/support/solutions/43000471705-how-to-purchase-additional-market-data/) | 主交易所实时数据和额外费用 | 2026-09-20 |
| [Market data coverage](https://www.tradingview.com/data-coverage/) | 各交易所延迟和价格 | 2026-09-20 |
| [Mastering watchlists](https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/) | 自选股、分组、导入、指标、新闻 | 2026-09-20 |
| [Watchlist advanced view](https://www.tradingview.com/support/solutions/43000771546-watchlist-advanced-view-mode/) | 财务、风险、技术、财报、新闻视图 | 2026-09-20 |
| [Stock Screener](https://www.tradingview.com/support/solutions/43000718866-tradingview-stock-screener-trade-smarter-not-harder/) | 基本面/技术字段和筛选器 | 2026-09-20 |
| [Introduction to alerts](https://www.tradingview.com/support/solutions/43000520149-introduction-to-tradingview-alerts/) | 价格、技术、watchlist 告警 | 2026-09-20 |
| [How to set up alerts](https://www.tradingview.com/support/solutions/43000595315-how-to-set-up-alerts/) | 条件、频率、邮件、App、webhook | 2026-09-20 |
| [Watchlist alerts](https://www.tradingview.com/support/solutions/43000739708-watchlist-alerts-your-trading-edge/) | 列表级条件告警行为 | 2026-09-20 |
| [Webhook alerts](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/) | Webhook 限制、安全和失败状态 | 2026-09-20 |
| [Hotlists](https://www.tradingview.com/support/solutions/43000762029-discover-market-movers-with-tradingview-hotlists/) | 成交量、涨跌、区间、跳空异动 | 2026-09-20 |
| [How to read financial statements](https://www.tradingview.com/support/solutions/43000760059-how-to-read-financial-statements/) | 三大财务报表 | 2026-09-20 |
| [Financial data differences](https://www.tradingview.com/support/solutions/43000540145-why-does-financial-data-differ-from-other-sources/) | 数据来源、标准化和原始报告差异 | 2026-09-20 |
| [Earnings](https://www.tradingview.com/support/solutions/43000629790-earnings/) | As reported、Standardized、Estimate、Surprise | 2026-09-20 |
| [Filter news by watchlist](https://www.tradingview.com/support/solutions/43000734013-filter-by-watchlist/) | Watchlist 新闻聚合 | 2026-09-20 |
| [TradingView social network](https://www.tradingview.com/support/solutions/43000761245-tradingview-social-network/) | 社区观点、Ideas、Minds | 2026-09-20 |
| [AI Screener](https://www.tradingview.com/support/solutions/43000785770-how-to-use-the-ai-screener/) | 自然语言筛选和限制 | 2026-09-20 |
| [Getting started with Supercharts](https://www.tradingview.com/support/solutions/43000746464-getting-started-with-supercharts/) | 历史回放、图表和保存布局 | 2026-09-20 |
| [Learn to trade on historical data](https://www.tradingview.com/support/solutions/43000691889-learn-to-trade-on-historical-data/) | Replay Trading 数据保存边界 | 2026-09-20 |
