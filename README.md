# FinSight AI Agent

《基于大语言模型与多智能体协作的智能金融分析 AI Agent》

FinSight = Finance + Sight，意为“金融洞察”。定位为个人投资者和金融分析学习者的智能金融研究与自选股监测系统。

该项目主要用于数据分析实习、AI 产品经理实习、数据产品或金融科技岗位的求职核心作品集，需要同时展示 Python、SQL、数据分析、金融分析、RAG、多 Agent、工具调用、记忆、评测、监控、产品设计和完整项目落地能力。

目标用户：关注美股但缺乏时间完成每日信息收集和系统分析的个人投资者，以及需要辅助完成金融研究的学习者。

## 当前状态

2026-09-21 已加入 Alpha Vantage `TIME_SERIES_DAILY` 离线日线 PoC，默认 compact；SEC live smoke 已完成，用户也已完成一次 NVDA 日线 live smoke，但行情供应商仍未冻结。已完成 n=3 真实线上语音访谈匿名聚合，仍属于小样本定性验证。

项目已完成文档初始化、官方竞品案头调研、PRD V1.0/P0-P2 优先级整理、六层数据架构建议、可点击 Web 原型和 SEC EDGAR/Company Facts 离线数据源 PoC。已新增离线 ResearchSnapshot synthetic 契约 PoC，并完成一次真实 NVDA 本地 saved_snapshot 装配；当前仍无完整可运行业务系统、数据库连接或实验结果；已完成一次用户执行的 NVDA 低频实时 smoke；基础 K 线预览与 Excel 导出预览已纳入当前 P0 原型闭环；真实 K 线功能和 Excel 文件生成仍未实现。`.codex/` 中的 Sol/Luna 模型和 low 推理配置只影响支持项目配置的后续会话，不能视为当前会话已经切换。本仓库中的架构、流程、竞品记录和原型均不能视为真实数据能力、实测结果或真实用户需求验证。

## 已确定的产品范围

1. 用户现场输入股票代码或公司名称，系统立即完成行情、技术面、基本面、新闻情绪、行业、宏观和风险分析。
2. 用户建立自选股列表，并为每只股票配置关注方向、涨跌幅阈值、成交量阈值和报告频率。系统进行分钟级异动监测，并在每日收盘后自动生成完整研究报告，通过系统消息和邮件发送。

- 12 个核心模块涵盖研究、自选股、监控、RAG、多 Agent、多空交叉辩论、风控、可视化、日报、LLMOps、自动复盘与 Agent 评测。
- 支持意图识别、任务路由、工具调用、多轮记忆和财报/公告/历史报告自然语言问答；Agent 角色拆分及 RAG 检索链路是待验证方案，按复杂度选择必要角色。
- 每个金融结论关联数据与来源，使用历史相似事件验证假设，采用 Point-in-Time 防止未来信息泄漏，保存判断并统计 Agent、事件类型和数据源的历史表现。
- MVP 只做美股正常交易时段监测，暂不含盘前盘后；免费或低成本行情允许 5–15 分钟延迟。供应商候选见数据源方案，最终选择须经过真实 API 测试；每用户自选股上限待限额核验。
- 保存每次判断及历史报告并在 5/20 个交易日后自动复盘。只做研究辅助，不提供确定性投资建议。不连接真实券商、不执行自动或真实交易、不承诺收益，不编造数据、API 和实验结果。

完整已确认背景见 [项目记忆](PROJECT_MEMORY.md)。

## 文件导航

离线 SEC EDGAR / Company Facts PoC 见 [SEC PoC](docs/poc/sec-data-poc.md)，覆盖 CIK、申报筛选、Company Facts 规范化和截止时间过滤；默认不联网。

| 文件 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 开发、测试、真实性与安全规则 |
| [PROJECT_MEMORY.md](PROJECT_MEMORY.md) | 已确定决策、建议和待确认问题 |
| [项目立项](docs/01-project-charter.md) | 项目目标、范围、交付边界 |
| [用户痛点](docs/02-user-pain-points.md) | 用户假设、场景与验证计划 |
| [竞品分析](docs/03-competitive-analysis.md) | 官方资料竞品矩阵、TradingAgents 分析和证据边界 |
| [竞品证据目录](docs/research/competitors/) | Yahoo Finance、TradingView、FinChat、Koyfin、OpenBB、TradingAgents 的逐项官方链接与核验记录 |
| [PRD V1.0](docs/04-prd.md) | P0/P1/P2 优先级、演示闭环、状态、输入输出和验收条件 |
| [原型设计](docs/10-prototype-design.md) | 可点击原型的信息架构、Mock 边界和可用性测试任务 |
| [技术方案](docs/05-technical-design.md) | 逻辑架构、Agent 协作与任务可靠性 |
| [数据源方案](docs/06-data-sources.md) | 数据需求、选型门槛和溯源规范 |
| [评测方案](docs/07-evaluation.md) | 质量评估、安全测试和复盘口径 |
| [开发计划](docs/08-development-plan.md) | 分阶段任务与完成条件 |
| [代码开发前任务书](docs/09-pre-code-handoff.md) | 可直接交给网页端 GPT 的开发就绪准备清单 |

## 标准化 Skills

| Skill | 职责 |
| --- | --- |
| [stock-research](skills/stock-research/SKILL.md) | 单只股票的证据驱动协作分析 |
| [financial-rag](skills/financial-rag/SKILL.md) | 金融资料检索、时间过滤及引用 |
| [market-monitor](skills/market-monitor/SKILL.md) | 分钟级异动识别、去重与告警 |
| [daily-report](skills/daily-report/SKILL.md) | 收盘报告、归档及投递流程 |
| [agent-evaluation](skills/agent-evaluation/SKILL.md) | Agent 评测、历史复盘与结果审计 |

这些 Skill 是项目内的工作流规范，尚未注册为运行时工具，也不会自动启动 Agent、监控、邮件或定时任务。当前仅运行离线检查与固定 fixture 测试，不连接新的外部服务。

## 建议下一步

SEC 适配器的离线边界验证和一次 NVDA 低频实时 smoke 已完成。下一步应在确认 SEC 使用政策、User-Agent、保存与再分发范围后，评估是否进行更严格的契约和持续性验证；这次 smoke 不代表生产稳定性。

[用户痛点验证计划](docs/02-user-pain-points.md)、[匿名访谈聚合](docs/research/user-interview-synthesis-001.md) 和 [PRD V1.0](docs/04-prd.md) 已更新。原型可用性测试由用户决定暂缓；当前继续推进离线 ResearchSnapshot 契约，后续再装配真实保存快照。在此之前不把 RAG、多 Agent、新闻或投递写成已实现能力。完整后续顺序见 [开发计划](docs/08-development-plan.md)。

## 阅读与协作

能力定位：数据分析是主轴，技术是基础，产品能力是加分项，AI Agent 是差异化优势。开发者背景、PRD 优先级和已确认决策见 PROJECT_MEMORY.md；痛点、优先级价值和竞品差异属于待验证假设，候选技术未冻结。

任务前阅读 AGENTS.md、PROJECT_MEMORY.md、相关 docs 和 Skill。项目文件是 ChatGPT 与本地 Codex 的共享记忆。已完成 n=3 真实访谈匿名聚合，仍未完成原型可用性测试、完整业务系统、真实评测、Beta 或部署；SEC 与 Alpha Vantage 各已完成一次用户执行的 live smoke，本轮不新增联网请求。固定 fixture 自动测试已完成，可点击原型已完成但真实可用性测试尚未完成，不以规划冒充成果。

后续代码任务使用 Sol 拆解、Luna 低推理执行、独立 Sol 低推理验收。项目已配置 GitHub `origin` 和任务完成后自动提交推送规则；每次是否同步成功以实际 push 输出和 commit ID 为准。竞品调研证据文件只代表截至 2026-09-20 的官方公开资料，功能、价格和版本变化后需要重新核验。

### ResearchSnapshot schema 1.1

当前已完成真实 NVDA 本地快照契约加固：使用本地 SEC ticker mapping 建立 NVDA→CIK 证据链，按 SEC 美国东部时间（含 DST）处理 acceptance 时间，并默认只保留 10-K、10-K/A、10-Q、10-Q/A、8-K、8-K/A。此轮不联网、不覆盖旧快照，也不代表完整 MVP。

ResearchSnapshot 1.1 的过滤统计已区分 Point-in-Time 排除、非目标表单和缺少可用时间；自动测试覆盖冬夏令时、表单过滤、身份校验和八文件合成装配。本轮仍未实现 Excel、RAG、LLM、Agent、数据库、前端真实接入或部署。

ResearchSnapshot 1.1 已增加离线 Excel 导出路径：导出器和 synthetic 测试已在本轮实现，真实文件只允许保存在被忽略的 `.local_data` 中；不连接网络，也不代表 RAG、Agent、数据库或前端已完成。
