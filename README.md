# FinSight AI Agent

《基于大语言模型与多智能体协作的智能金融分析 AI Agent》

FinSight = Finance + Sight，意为“金融洞察”。定位为个人投资者和金融分析学习者的智能金融研究与自选股监测系统。

该项目主要用于数据分析实习、AI 产品经理实习、数据产品或金融科技岗位的求职核心作品集，需要同时展示 Python、SQL、数据分析、金融分析、RAG、多 Agent、工具调用、记忆、评测、监控、产品设计和完整项目落地能力。

目标用户：关注美股但缺乏时间完成每日信息收集和系统分析的个人投资者，以及需要辅助完成金融研究的学习者。

## 当前状态

项目处于文档初始化阶段。尚无可运行系统、依赖配置、API 连接或实验结果。本仓库中的架构、流程和验收规则是后续开发依据，不能视为已实现能力。

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

| 文件 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 开发、测试、真实性与安全规则 |
| [PROJECT_MEMORY.md](PROJECT_MEMORY.md) | 已确定决策、建议和待确认问题 |
| [项目立项](docs/01-project-charter.md) | 项目目标、范围、交付边界 |
| [用户痛点](docs/02-user-pain-points.md) | 用户假设、场景与验证计划 |
| [竞品分析](docs/03-competitive-analysis.md) | 竞品调研维度和证据要求 |
| [PRD](docs/04-prd.md) | 功能需求、用户流程与验收条件 |
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

这些 Skill 是项目内的工作流规范，尚未注册为运行时工具，也不会自动启动 Agent、监控、邮件或定时任务。当前无需安装或运行任何程序。

## 建议下一步

[用户痛点验证计划](docs/02-user-pain-points.md)已准备好，包含提问与空白记录模板。下一步找一位最近研究过美股或读过财报的人，收集一次真实任务经历作为初步验证；暂不开始业务开发。完整后续顺序见 [开发计划](docs/08-development-plan.md)。

## 阅读与协作

能力定位：数据分析是主轴，技术是基础，产品能力是加分项，AI Agent 是差异化优势。开发者背景与已确认决策见 PROJECT_MEMORY.md；痛点和竞品差异属于待验证假设，候选技术未冻结。

任务前阅读 AGENTS.md、PROJECT_MEMORY.md、相关 docs 和 Skill。项目文件是 ChatGPT 与本地 Codex 的共享记忆。当前未完成访谈、竞品调研、API 测试、原型、业务代码及自动测试、真实评测、Beta 或部署；不以规划冒充成果。

后续代码任务使用 Sol 指挥、Luna Max 执行、独立 Sol 验收。项目已配置 GitHub `origin` 和任务完成后自动提交推送规则；每次是否同步成功以实际 push 输出和 commit ID 为准。
