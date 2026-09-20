# Yahoo Finance 竞品证据卡

> 调研状态：已完成官方资料核验，未注册付费账号，未登录测试 Premium/Gold 功能，未调用 Yahoo API。
>
> 核验日期：2026-09-20（Asia/Shanghai）。
>
> 证据口径：本文只把 Yahoo Finance 官网、Yahoo Help、官方定价页和 Yahoo Finance 官方公告列为主要证据。带“官方宣称（未实测）”的内容来自官方页面描述；没有在官方资料中找到明确信息的内容标为“未知”。本文不是用户需求验证，也不替代真实产品试用或数据许可核验。

## 产品定位与证据边界

Yahoo Finance 是面向关注金融市场和商业新闻的投资者的信息、行情、组合和研究平台。官方入门页列出报价、新闻、评论、分析、交互式图表、筛选器、市场事件日历和 My Portfolio 等能力；订阅页把 Free Plan 描述为面向对金融市场和突发商业新闻感兴趣的投资者。这里的目标用户判断是对官方产品定位的归纳，不是用户调研结论。

- [Getting started with Yahoo Finance](https://help.yahoo.com/kb/SLN3642.html)（官方 Help；核验日期：2026-09-20）
- [Yahoo Finance Premium plans](https://finance.yahoo.com/about/plans/select-plan/)（官方定价页；核验日期：2026-09-20）

Yahoo Finance 的页面和订阅能力会随地区、设备、登录状态、证券和数据许可变化。以下表格记录官方资料当日能确认的范围；没有进行登录、付费或跨地区验证。

## 统一能力矩阵

| 维度 | 官方证据与当前结论 | 状态 |
| --- | --- | --- |
| 目标用户 | 官方入门页覆盖股票、基金、ETF、市场新闻、分析和组合跟踪；定价页称免费计划面向关注金融市场和商业新闻的投资者。 | 官方宣称；未实测 |
| 美股行情及延迟情况 | Yahoo Help 称许多交易所提供实时流式报价，但并非所有市场实时；网页报价页显示该报价是实时还是延迟。官方交易所表按市场列出延迟和数据提供商，不能把“Yahoo Finance”概括为统一的实时或统一的延迟。 | 官方宣称；未实测 |
| 股票搜索 | 可用股票代码或公司名搜索公司、基金、证券；帮助页还列出 ETF、指数、商品、共同基金和加密货币等搜索对象。 | 官方宣称；未实测 |
| 自选股/组合 | My Portfolio 支持创建 watchlists、多个 portfolios、导入/导出和自定义视图；帮助页说明可添加、排序和删除 ticker。组合还可用于实际、潜在或虚拟持仓跟踪。 | 官方宣称；未实测 |
| 价格、成交量及新闻告警 | 官方帮助页确认自定义价格告警和移动推送；通知页列出价格变化、52 周高低、财报结果、公司新闻、市场新闻、晨报及组合日/周摘要。官方资料没有在本次核验中给出一个统一的“成交量异常告警”说明。 | 价格/新闻：官方宣称；成交量异常：未知；未实测 |
| 基本面和财务分析 | Quote pages 提供 Statistics、Historical Data、Financials、Analysis、Holders、Options 等标签；Financials 包含年度/季度损益表、资产负债表和现金流，Analysis 包含盈利/收入/增长估计、盈利历史和 EPS 修订。Premium 页面另列历史财务、估值、技术指标、研究报告和风险分析。 | 官方宣称；未实测 |
| 新闻与情绪分析 | 官方入门页列出财经新闻、突发报道、深度分析和评论；Premium 页面列出 Community Insights、Financial Times、MT Newswires 等内容。官方资料没有明确证明对美股新闻做可复现的机器情绪分类或因果归因。 | 新闻聚合/社区洞察：官方宣称；自动新闻情绪：未知；未实测 |
| 财报及公告问答 | Quote pages 和 Premium 页面提供财务数据、历史 earnings call transcripts、公司研究报告等研究材料。官方 Yahoo Scout 公告称可在部分股票报价页和新闻文章中提问，并给出基于 Yahoo Finance 数据和权威网络来源的上下文回答；本次未登录验证财报问答、8-K/10-K 定位或回答覆盖范围。 | Yahoo Scout 问答：官方宣称；财报/公告问答完整性：未知；未实测 |
| 引用和原文定位 | Yahoo Scout 官方公告称回答来自 Yahoo Finance 数据和权威网络来源；页面没有在本次核验中承诺每个数字都返回原始文件、页码、段落或可审计引用链。 | 来源范围：官方宣称；逐结论原文定位：未知；未实测 |
| AI 分析能力 | Yahoo Finance 官方公告介绍 Yahoo Scout：可在选定股票报价页和新闻文章中回答股票或公司资产负债表问题，并提供上下文答案；官方公告没有披露多 Agent 架构、提示版本、评测指标或回答准确率。 | 官方宣称；未实测 |
| 多 Agent 协作 | 官方资料核验范围内未找到 Yahoo Finance 使用多个协作 Agent、角色路由或裁判机制的说明。 | 未知 |
| 多空观点与风险审查 | Premium 提供专家选股、研究报告、Fair Value 等内容；官方资料未说明系统会生成独立多头/空头辩论、证据审计或风控阻断。 | 未知 |
| 每日收盘报告 | 通知页和 Premium 页列出晨报、每日/每周组合摘要及订阅者日报/Market Digest；没有找到按用户自选股在美股收盘后生成完整多维研究报告的明确说明。 | 日报/摘要：官方宣称；收盘研究报告：未知；未实测 |
| 邮件或系统通知 | 官方通知页列出公司新闻、市场新闻、财报、晨报和组合摘要；移动帮助页确认推送通知。Premium 页面列出每日邮件。邮件/推送的具体地区和套餐资格需以账户界面为准。 | 官方宣称；未实测 |
| 历史报告 | 官方提供历史价格、股息、拆股、财务数据、研究报告和 earnings call transcripts（部分为 Premium）；未找到由 Yahoo Finance 自动生成的、可按用户判断版本归档的历史分析报告功能说明。 | 历史数据/研究材料：官方宣称；历史生成报告：未知；未实测 |
| 历史判断复盘 | 官方资料核验范围内未找到保存一次 AI 判断并在 5/20 个交易日后按事实、归因、风险和方向自动复盘的说明。 | 未知 |
| 数据可视化 | 官方入门页确认交互式图表，可按时间范围、指标和参数绘制并比较多个标的；Premium 页列出高级图表、技术图表模式、组合风险/分散度可视化和 AlphaSpace。 | 官方宣称；未实测 |
| 免费版本限制及价格 | 官方订阅页显示 Free Plan；同一官方定价页当前展示 Bronze $7.95/月（按年计费 $95.40）、Silver $19.95/月（按年计费 $239.40）、Gold $39.95/月（按年计费 $479.40），并列出各档组合、研究、数据、新闻、图表和告警权益。具体可用性可能依地区、设备和产品迁移变化。 | 官方宣称；未购买/未实测 |

## 重点证据整理

### 行情、数据覆盖与延迟

Yahoo 官方 Help 明确要求用户在报价下方查看交易所和实时/延迟标记。官方交易所与数据提供商页面还按市场列出 delay、provider 和覆盖情况，例如部分美国指数为实时或 15 分钟，其他市场可能有不同延迟。由于页面按交易所和资产类型区分，FinSight 不能只引用 Yahoo Finance 的品牌名判断延迟；若未来参考 Yahoo 数据，必须记录具体市场、source、event time、retrieved time 和页面标示的实时/延迟状态。

- [Check real-time data in Yahoo Finance for Web](https://help.yahoo.com/kb/SLN2321.html)（官方 Help；核验日期：2026-09-20）
- [Exchanges and data providers on Yahoo Finance](https://help.yahoo.com/kb/SLN2310.html)（官方 Help；核验日期：2026-09-20）

### 搜索、组合和提醒

官方帮助页确认可用 ticker 或公司名查找报价，并把证券添加到 watchlist。My Portfolio 支持多个列表、组合、导入/导出和组合注释；移动端帮助页确认自定义价格目标达到后可推送。官方通知设置还列出 earnings、company news、market news、morning brief、daily summary 和 weekly summary，但本次没有登录账户验证各项的默认开关、限额和实际送达。

- [Find quotes, business news, and market info](https://help.yahoo.com/kb/SLN2340.html)（官方 Help；核验日期：2026-09-20）
- [Track investments using My Portfolio](https://help.yahoo.com/kb/SLN7034.html)（官方 Help；核验日期：2026-09-20）
- [Set and manage custom price alerts for iOS](https://help.yahoo.com/kb/SLN31006.html)（官方 Help；核验日期：2026-09-20）
- [Yahoo Finance notifications](https://finance.yahoo.com/notifications)（官方通知页；核验日期：2026-09-20）

### 财务、研究材料与引用边界

官方 quote page 帮助文档列出财务报表、估计、盈利历史、EPS 修订、历史数据、持有人和期权等研究标签。Premium/订阅页列出历史财务、研究报告、earnings call transcripts、技术图表和筛选器。上述页面证明的是材料和字段存在，并不证明系统会把每个数字追溯到 SEC 原始文件的具体页码或段落，也不证明这些材料适合作为 Point-in-Time 回测的原始快照。

- [Research stocks, mutual funds and ETFs with quote pages](https://help.yahoo.com/kb/SLN28277.html)（官方 Help；核验日期：2026-09-20）
- [Yahoo Finance Premium benefits](https://finance.yahoo.com/subscriptions/)（官方订阅页；核验日期：2026-09-20）
- [Download historical data](https://help.yahoo.com/kb/sln2311.html)（官方 Help；核验日期：2026-09-20）

### Yahoo Scout 与 AI 研究

Yahoo Finance 2026-06-03 的官方公告称，Yahoo Scout 已嵌入部分股票报价页和新闻文章，能够回答股票和公司资产负债表相关问题，并使用 Yahoo Finance 数据及权威网络来源生成上下文答案。该公告没有提供可复现的测试数据、模型版本、引用格式、失败率、评测集、Agent 角色或风险审查流程。本项目只记录为官方产品声明，未把它写成实测能力或效果结论。

- [Yahoo announces AI-powered experiences for Yahoo Finance and Yahoo Sports](https://finance.yahoo.com/markets/article/yahoo-announces-ai-powered-experiences-for-yahoo-finance-and-yahoo-sports-200417714.html)（Yahoo Finance 官方公告；发布于 2026-06-03；核验日期：2026-09-20）

## 对 FinSight 的可比启示

### 已被 Yahoo Finance 官方产品覆盖的方向

- 代码/公司名搜索、报价页、交互式图表、基本财务字段、新闻与事件日历、组合/自选股和常见价格/新闻/财报通知已有较完整覆盖。
- Premium 进一步覆盖历史价格和财务数据下载、研究报告、earnings call transcripts、技术图表、组合风险和多种筛选器。
- Yahoo Scout 已公开宣称把自然语言问题和金融数据/新闻上下文结合，FinSight 不能把“自然语言问股票”本身当作独占创新。

### 仍需用证据核验、不能预先宣称空白的方向

- 逐结论证据链是否能定位到原始文件、时间和位置：Yahoo 官方材料只说明来源范围，详细引用格式未知。
- 是否支持按分析时点冻结数据、保存判断版本并在 5/20 个交易日后复盘：Yahoo 官方资料未给出说明，但这不能直接写成“Yahoo 不支持”。
- 多空独立论证、Evidence Auditor、风险阻断、历史相似事件和 Agent 表现统计：官方资料未披露，具体能力未知。
- 按用户自选股、数据截止时间和许可状态生成可审计收盘报告：官方有摘要、晨报和邮件权益，但完整流程与字段未知。

### 需要避免重复造轮子的方向

如果 FinSight 只做搜索、价格展示、自选股、K 线、基础财务、新闻聚合、常规价格提醒和简单组合摘要，功能上会与 Yahoo Finance 的官方覆盖高度重叠。更有区分度的候选方向应放在证据链、时间顺序与 Point-in-Time、可解释的多空反证、风险审查、判断登记和 5/20 个交易日复盘，并通过实际评测证明价值；这些仍是 FinSight 的设计方向，不是已验证竞争优势。

## 未知项与后续核验清单

以下内容在本次官方公开资料核验中未得到足够证据，统一保留为未知或未实测：

1. Yahoo Finance 各美国交易所、盘前/盘后和具体 ticker 的实际报价延迟、刷新周期及限流。
2. Free、Bronze、Silver、Gold 在不同地区的完整告警额度、新闻版权、下载权限和 AlphaSpace/Yahoo Scout 可见范围。
3. Yahoo Scout 的模型、工具调用、上下文窗口、引用定位、错误恢复和实际回答准确率。
4. 是否提供股票新闻自动情绪分数、自动原因归因、独立多空辩论、风险审查或多 Agent 编排。
5. 是否可以保存用户生成的完整分析报告、版本化判断并自动执行 5/20 个交易日复盘。
6. 研究报告、新闻、历史财务和 transcripts 的再分发、缓存、展示及项目使用许可。
7. 邮件、浏览器通知和移动推送的真实送达率、去重/冷却策略和 API 访问方式。

## 来源清单

| 官方来源 | 用途 | 核验日期 |
| --- | --- | --- |
| [Getting started with Yahoo Finance](https://help.yahoo.com/kb/SLN3642.html) | 产品范围、搜索、图表、筛选器、新闻、组合 | 2026-09-20 |
| [Find quotes and market info](https://help.yahoo.com/kb/SLN2340.html) | 代码/公司名搜索 | 2026-09-20 |
| [Check real-time data for Web](https://help.yahoo.com/kb/SLN2321.html) | 实时/延迟标记 | 2026-09-20 |
| [Exchanges and data providers](https://help.yahoo.com/kb/SLN2310.html) | 市场延迟和数据提供商 | 2026-09-20 |
| [Quote pages research](https://help.yahoo.com/kb/SLN28277.html) | 财务、分析、历史数据、估计 | 2026-09-20 |
| [My Portfolio toolkit](https://help.yahoo.com/kb/SLN7034.html) | 自选股、组合、导入/导出、组合跟踪 | 2026-09-20 |
| [Custom price alerts for iOS](https://help.yahoo.com/kb/SLN31006.html) | 价格提醒和推送 | 2026-09-20 |
| [Yahoo Finance notifications](https://finance.yahoo.com/notifications) | 新闻、价格、财报和组合通知 | 2026-09-20 |
| [Premium plans](https://finance.yahoo.com/about/plans/select-plan/) | 免费/付费方案与价格 | 2026-09-20 |
| [Premium benefits](https://finance.yahoo.com/subscriptions/) | 历史数据、研究报告、transcripts、Premium Alerts | 2026-09-20 |
| [Download historical data](https://help.yahoo.com/kb/sln2311.html) | 历史数据下载限制 | 2026-09-20 |
| [Yahoo Scout announcement](https://finance.yahoo.com/markets/article/yahoo-announces-ai-powered-experiences-for-yahoo-finance-and-yahoo-sports-200417714.html) | 官方 AI 研究能力声明 | 2026-09-20 |
