# FinChat 竞品证据

核验日期：2026-09-20。
研究状态：仅查阅 FinChat 官方产品页、官方帮助/文档、官方定价页和官方博客；没有注册付费账号，没有绕过付费墙，也没有对产品功能进行实测。下文的“官方宣称”表示官方资料中的产品描述，不等于本项目已经复现或验证。

## 资料范围与证据规则

FinChat 的公开资料中同时出现 FinChat、FinChat Copilot、FinChat Terminal 以及由 FinChat 提供的嵌入/数据文档。本文将它们视为同一产品体系的不同公开资料入口，但不把嵌入文档中的可配置能力直接等同于普通用户套餐能力。

证据状态只使用以下三类：

- **官方宣称**：官方页面明确描述了该能力或限制。
- **未知**：截至核验日期，查阅到的官方资料没有明确说明，不能据此断言支持或不支持。
- **未实测**：没有登录、付费或实际操作，因此不报告运行成功、回答质量或延迟实测结果。

## 官方来源清单

| 编号 | 官方来源 | 主要用途 | 核验日期 |
| --- | --- | --- | --- |
| F1 | [FinChat 产品首页](https://finchat.io/) | 产品定位、Copilot、数据、Dashboard、通知、可视化 | 2026-09-20 |
| F2 | [FinChat 定价页](https://finchat.io/pricing/) | 套餐、免费额度、数据历史、事件和通知权益 | 2026-09-20 |
| F3 | [FinChat Help Center](https://finchat.io/help/) | 官方帮助主题目录及功能范围 | 2026-09-20 |
| F4 | [FinChat 数据文档](https://docs.finchat.io/embed-legacy/partner-portal/data) | 数据覆盖、数据供应方、SEC/电话会来源 | 2026-09-20 |
| F5 | [How to Use FinChat](https://finchat.io/blog/how-to-use-finchat/) | 搜索公司、Dashboard、watchlist 和通知示例 | 2026-09-20 |
| F6 | [Introducing FinChat V3](https://newsletter.finchat.io/p/introducing-finchat-v3) | Copilot 对财报、电话会和比较任务的官方描述 | 2026-09-20 |
| F7 | [FinChat Copilot: The Complete AI for Investors](https://finchat.io/blog/finchat-copilot-the-complete-ai-for-investors/) | 官方 AI、来源链接、数据类型和评测宣传 | 2026-09-20 |
| F8 | [FinChat 与 Stratosphere 合并公告](https://finchat.io/blog/finchat-and-stratosphere-merge/) | Dashboard、watchlist、通知和公司数据覆盖描述 | 2026-09-20 |
| F9 | [FinChat 自定义数据文档](https://docs.finchat.io/embed-legacy/partner-portal/custom-data) | 嵌入 Copilot 的自定义数据、source 字段和 sentiment 接口示例 | 2026-09-20 |

## 产品概况

官方首页将 FinChat 定位为面向公共市场投资者的现代金融数据终端，强调全球股票、ETF、基金、基本面数据、Copilot、公司 KPI、Dashboard、数据可视化和通知。官方定价页把股票、ETF 和基金覆盖写为全球市场 100,000+ 公司；数据文档把基本面数据供应方写为 S&P Global，报告与新闻材料主要包含 SEC filings，电话会文本来源写为 FMP。上述是官方口径，不代表本项目已经核验数据完整性或许可范围。[F1](https://finchat.io/) [F2](https://finchat.io/pricing/) [F4](https://docs.finchat.io/embed-legacy/partner-portal/data)（核验：2026-09-20）

## 能力核对

| 比较维度 | 官方资料能确认的内容 | 证据状态与边界 |
| --- | --- | --- |
| 目标用户 | 官方首页称其服务公共市场投资者；官方博客把使用者描述为基本面投资者，并举例个人和专业投资者使用研究终端。 | **官方宣称**。没有真实用户规模、用户画像分布或用户访谈证据；[F1](https://finchat.io/) [F7](https://finchat.io/blog/finchat-copilot-the-complete-ai-for-investors/)（核验：2026-09-20） |
| 美股行情及延迟 | 官方数据文档称覆盖全球股票，并描述 50,000+ 股票的实时和历史市场数据；产品页也使用“real-time”描述。美国股票的具体交易所、不同套餐、延迟分布、时间戳字段和异常时的降级规则没有在公开资料中完整展开。 | **官方宣称**有实时市场数据；具体延迟与条件为**未知**；未登录核验。[F1](https://finchat.io/) [F4](https://docs.finchat.io/embed-legacy/partner-portal/data)（核验：2026-09-20） |
| 股票搜索 | 官方博客说明可在顶部搜索栏输入公司名称或 ticker；官方博客还描述了筛选器和公司搜索。 | **官方宣称**；没有实测歧义证券、交易所筛选和搜索耗时。[F5](https://finchat.io/blog/how-to-use-finchat/) [F8](https://finchat.io/blog/finchat-and-stratosphere-merge/)（核验：2026-09-20） |
| 自选股/组合 | 官方产品页和博客描述可建立 Dashboard、portfolio 和 watchlist，按指标组织公司；定价页列有 Dashboard 数量和行数限制，并在付费档列出 Portfolio Stats。 | **官方宣称**；具体 watchlist 上限、分组、关注理由和跨设备同步细节为**未知**；未实测。[F1](https://finchat.io/) [F2](https://finchat.io/pricing/) [F5](https://finchat.io/blog/how-to-use-finchat/)（核验：2026-09-20） |
| 价格、成交量及新闻告警 | 官方博客称通知可覆盖 press release、SEC filings、conference calls 和其他重要公告；产品页称有个性化通知。公开资料没有明确写出价格阈值、成交量阈值、波动率规则或冷却/合并机制。 | 通知为**官方宣称**；价格/成交量异动告警、去重和冷却为**未知**；未实测。[F1](https://finchat.io/) [F5](https://finchat.io/blog/how-to-use-finchat/) [F2](https://finchat.io/pricing/)（核验：2026-09-20） |
| 基本面和财务分析 | 官方定价页列出财务报表与比率、KPI/segments、估值、DCF、行业比较、分析师估计、所有权等功能；数据文档称基本面覆盖 100,000+ 公司、KPI/segments 覆盖 2,000+ 公司。 | **官方宣称**；没有本项目所需的独立字段完整率、计算口径或数字准确率实测。[F2](https://finchat.io/pricing/) [F4](https://docs.finchat.io/embed-legacy/partner-portal/data)（核验：2026-09-20） |
| 新闻与情绪分析 | 官方首页列出 curated news；官方数据文档描述报告、新闻及电话会文本。官方自定义数据文档给出 `getStockSentiment` 作为接入自有 sentiment 数据的示例，但这不能证明普通套餐内置了同等情绪模型。 | 新闻聚合为**官方宣称**；原生新闻情绪评分、情绪时间序列和解释粒度为**未知**。自定义 sentiment 接口属于嵌入/平台文档；未实测。[F1](https://finchat.io/) [F4](https://docs.finchat.io/embed-legacy/partner-portal/data) [F9](https://docs.finchat.io/embed-legacy/partner-portal/custom-data)（核验：2026-09-20） |
| 财报及公告问答 | 官方 Copilot 资料称可访问 filings、transcripts、financials、company presentations 和 real-time news；V3 介绍用“总结电话会/年度报告、比较公司”等示例说明自然语言研究。数据文档明确报告/公告数据来自 SEC filings。 | **官方宣称**有面向投资研究的问答和总结；未进入产品验证回答是否覆盖 10-K/10-Q/8-K、表格和跨文档检索。[F4](https://docs.finchat.io/embed-legacy/partner-portal/data) [F6](https://newsletter.finchat.io/p/introducing-finchat-v3) [F7](https://finchat.io/blog/finchat-copilot-the-complete-ai-for-investors/)（核验：2026-09-20） |
| 引用和原文定位 | 官方博客宣称回答可提供直接来源，且其他官方资料把 source URL、PDF、text、data 作为 Copilot 卡片的来源结构。公开资料没有证明普通用户回答一定显示页码、段落、表格单元格或 SEC 原文锚点。 | 链接级来源为**官方宣称**；精确原文定位为**未知**；未实测。[F7](https://finchat.io/blog/finchat-copilot-the-complete-ai-for-investors/) [F9](https://docs.finchat.io/embed-legacy/partner-portal/custom-data)（核验：2026-09-20） |
| AI 分析能力 | 官方称有 Ask FinChat/Copilot，可回答投资问题、总结报告和电话会、比较公司、生成图表或研究内容；官方还宣传其针对金融问题的专用能力。官方博客中的质量数字是 FinChat 自己的宣传，不能作为本项目实验证据。 | AI 功能为**官方宣称**；未登录、未运行同一问题集，不能写成实测通过或性能结论。[F6](https://newsletter.finchat.io/p/introducing-finchat-v3) [F7](https://finchat.io/blog/finchat-copilot-the-complete-ai-for-investors/)（核验：2026-09-20） |
| 多 Agent 协作 | 查阅的官方产品页、帮助页、定价页和 Copilot 资料没有明确公开多 Agent 编排、角色协作或可审计的 Agent 图。 | **未知**；不能据此断言不支持。未实测。[F1](https://finchat.io/) [F3](https://finchat.io/help/)（核验：2026-09-20） |
| 多空观点与风险审查 | 公开资料展示基本面研究、估值和 Copilot，但没有明确描述独立多头/空头观点、反证流程、风控 Agent 或证据阻断机制。 | **未知**；不能据此断言不支持。未实测。[F1](https://finchat.io/) [F6](https://newsletter.finchat.io/p/introducing-finchat-v3)（核验：2026-09-20） |
| 每日收盘报告 | 官方页面描述 Dashboard、AI summaries、notifications、公司事件和研究输出，但没有找到“按用户自选股在每日收盘后自动生成完整报告”的明确公开说明。 | **未知**；不要将 Dashboard 或单次 Copilot 输出当作收盘日报。未实测。[F1](https://finchat.io/) [F2](https://finchat.io/pricing/)（核验：2026-09-20） |
| 邮件或系统通知 | 官方产品页、博客和定价页确认有 notifications；官方博客展示站内通知入口。公开页面没有完整说明邮件、移动推送、通知模板、订阅偏好和投递状态。 | 站内通知为**官方宣称**；邮件和投递状态为**未知**；未实测。[F1](https://finchat.io/) [F5](https://finchat.io/blog/how-to-use-finchat/) [F2](https://finchat.io/pricing/)（核验：2026-09-20） |
| 历史报告 | 官方资料明确提供历史财务、财报/filings、电话会和事件访问；官方博客描述报告、图表和导出。对“系统生成的每次分析报告按日期、版本和证据快照保存”的能力没有明确说明。 | 历史资料访问为**官方宣称**；历史 AI 报告库、版本和证据快照为**未知**；未实测。[F2](https://finchat.io/pricing/) [F4](https://docs.finchat.io/embed-legacy/partner-portal/data) [F6](https://newsletter.finchat.io/p/introducing-finchat-v3)（核验：2026-09-20） |
| 历史判断复盘 | 未找到官方资料说明 FinChat 会在 5/20 个交易日后回看历史判断、区分事实/归因/风险/方向并统计 Agent 表现。 | **未知**；不能据此断言不支持。未实测。[F1](https://finchat.io/) [F3](https://finchat.io/help/)（核验：2026-09-20） |
| 数据可视化 | 官方首页列出 Data Visualization；官方博客描述基本面图表、公司比较、图表导出和支持图表/报告的 Copilot 输出。 | **官方宣称**；未核对图表指标、数据时间、单位、缺失值和引用是否始终显示。[F1](https://finchat.io/) [F6](https://newsletter.finchat.io/p/introducing-finchat-v3) [F8](https://finchat.io/blog/finchat-and-stratosphere-merge/)（核验：2026-09-20） |
| 免费版本限制及价格 | 定价页核验时显示 Free：5 年/6 个季度财务数据、2 年/2 个季度 KPI、每月 10 次 Copilot、1 个 Dashboard/30 行、3 个事件、1 年/1 个季度估计；Plus：$24/月、每月 100 次 Copilot；Pro：$64/月、每月 500 次 Copilot；另有 Enterprise 联系销售。页面写明年付最多节省 20%，但年付金额需切换页面确认。 | **官方定价页当前显示**；价格和权益可能变化，未购买或实测。免费 2 周 Pro trial 也在页面显示，但本文未注册。[F2](https://finchat.io/pricing/)（核验：2026-09-20） |

## 对 FinSight 的可比启示

以下是基于官方资料的产品差异观察，不是用户需求已验证结论，也不是对 FinChat 质量的贬低。

1. FinChat 已将全球基本面数据、公司 KPI、财报/电话会内容、图表和 Copilot 放在同一研究终端中；FinSight 不应把“能搜索财务数字、做基本图表或总结电话会”单独包装为充分差异化。
2. FinChat 官方资料明确强调来源链接、公司数据和研究内容，但公开资料没有给出 FinSight 所需的可审计证据链细节，例如截止时间过滤、页/段/表定位、时间顺序校验和证据不足时阻断结论。FinSight 若选择此方向，必须用实际实现和评测证明，而不能仅增加一个“引用”字段。
3. FinChat 的公开资料没有明确披露多 Agent、多空交叉质疑、5/20 个交易日判断复盘或按 Agent/事件/数据源统计表现。它们可以作为 FinSight 的待验证差异方向，但不能在竞品调研中写成“竞品没有”。
4. FinChat 已有 Dashboard、watchlist 和通知；FinSight 的分钟级监测、告警冷却/合并、源延迟与检测延迟分离、收盘日报和可复盘判断，需要通过具体流程设计形成差异，而不是只复制自选股和通知入口。

## 未知项与后续核验边界

- 普通用户套餐的实时数据按交易所、证券和市场时段的实际延迟、历史价格时间戳、成交量数据和数据许可细节未知。
- 普通 FinChat Copilot 是否始终返回可点击的原始文件位置、是否显示页码/段落/表格单元格、是否保留截止时间和版本未知。
- 原生新闻情绪、价格/成交量阈值告警、自动日报、邮件通知、历史分析版本、5/20 日复盘和多 Agent 架构未知。
- 本次没有通过账号操作验证任何上述功能，不产生“实测通过”结论。

## 与模拟访谈的关系

`docs/research/simulated-interview-001.md` 是模拟访谈，只能作为设计参考。FinChat 的官方资料不能替代真实用户访谈，也不能把本文件中的竞品能力描述写成用户需求已验证证据。
