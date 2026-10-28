# Evidence Auditor 提示词配对对照（开发诊断）

状态：2026-10-28 完成一次本地实验；**候选 V1 未启用，默认仍为 baseline**。这是同一组构造主张上的一次观察，参考标签为代理预标注，待用户人工复核，不代表真实用户场景准确率或上线能力。

## 样本与冻结

- 使用本机已保存的 AMD、AVGO、INTC、QCOM SEC 正文。每家公司选两个不同 filing，共 8 个窗口；每窗口构造一条直接支持和一条改变关键限定的非支持主张，共 16 个关联检查项。与旧跨公司诊断窗口无重叠，未把更换 ID 当作新证据。现有证据窗口生成函数和 400 字符限制保持不变。
- 参考标签在模型调用前单独冻结：`supported` 8、`contradicted` 6、`unsupported` 2。由独立只读代理在未见本轮模型输出时审阅；仍不是人工 gold。固定种子 `20261028`，16 项中 baseline 与 candidate-v1 各有 8 项先运行。
- 冻结输入 SHA-256：`e3056bb2abe50dbc0647812d94931a53e7db5184257e17b2ed29ce82dc2763af`；参考 SHA-256：`e6d7a2bb3dcaaf3296dc09f96450aa1873cfeec17a3078128c64b4552d24aad5`；事前封存清单 SHA-256：`19b0f226b06bf7c1c22f9a3ec11a2dd6b654173ba473fdd89326acd5cbec6027`。完整窗口、主张、参考依据和盲审记录仅在 Git 忽略目录 `.local_data/reviews/sec-auditor-prompt-paired-2026-10-28-001/`。
- 本地完整逐项对照 `comparison.json` SHA-256：`19aa6af5cafedc28039f955be8fe72340893a11db4b3547c0dc64d9f9abe3428`；可读版 `comparison.md` SHA-256：`d61e51e3a0ec6c993f4634c4cdb5ea0d08c3f9c82fe3c7b89d97e6aaa4989fcd`。独立文件哈希清单为同目录的 `artifact-hashes.json`；这些文件均不提交。
- 模型为本机 `qwen3:4b`，digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`；baseline 提示词 SHA-256 `1e676b20e7d0e499ff660d0c7d2a724e4d1fbebb182b21e446eb7106c33cd674`，candidate-v1 为 `cea2b77988d54ee92227502fc277fb6a834116d7408b98596febf20ad7de2d99`。两版本实际请求经核对只有系统提示词不同：当前项主张、窗口、来源、Schema、模型、`stream=false` 与 `think=false` 一致；无共享对话历史、无参考标签入模。

## 运行与结果

先用 `--prompt-version baseline` 或 `--prompt-version candidate-v1` 准备请求（默认零调用），确认模型 digest 后，按预先固定顺序逐项运行；每个版本每项只调用一次，没有重试。旧冻结 D002 的标签及独立更正建议保持原样，本实验不依赖其人工确认，也未重跑旧样本。可复核本机完整实验的汇总命令：

```bash
python3 .local_data/reviews/sec-auditor-prompt-paired-2026-10-28-001/summarize_comparison.py
```

该命令**仅重算保存记录，不调用模型**。单次准备入口示例：

```bash
PYTHONPATH=src python3 scripts/run_evidence_auditor.py \
  .local_data/reviews/sec-auditor-prompt-paired-2026-10-28-001/pair-inputs/T001.json \
  --output-dir .local_data/reviews/sec-auditor-prompt-paired-2026-10-28-001/prepared/example-candidate \
  --prompt-version candidate-v1
```

实际运行时间为 2026-10-28 09:12:58–09:15:06 UTC；本地 `/api/chat` **32 次**（每版本 16 次）、无重试，SEC/行情/模型下载请求 0。按单项记录累计耗时 baseline `50,923.486 ms`、candidate-v1 `73,228.438 ms`；包括进程与存储开销的整轮墙钟约 127.8 秒。单项耗时见本地 `comparison.json`。

| 口径（每版本分母均为 16） | baseline | candidate-v1 |
| --- | ---: | ---: |
| 接受 | 16 | 14 |
| 校验失败 | 0 | 2 |
| 运行失败 / 未执行 | 0 / 0 | 0 / 0 |
| 8 条直接支持主张中，接受且判 supported | 7 | 7 |
| 8 条非支持主张中，接受且误判 supported | 3 | 4 |
| 接受且与代理参考标签完全相同 | 9 | 9 |
| 接受输出：supported / partially_supported / unsupported / contradicted / uncertain | 10 / 0 / 3 / 3 / 0 | 11 / 1 / 0 / 2 / 0 |

候选修正了 baseline 在 **T004**（QCT 同比 17% 对 7%）、**T009**（AMD 51 亿美元换算）及 **T011**（股息 6.25 对 5.25 美元）的分类；**T001**、**T016** 从 baseline 的精确参考匹配退化为候选误判支持。**T013** 两版均为 accepted/supported，而冻结参考为 contradicted，属于双方共同语义错误，不能列为 baseline 正确→候选新增错误。**T007**、**T014** 的候选摘录不在配对窗口，属于校验失败，不计为候选语义正确或错误。T005 对“打算”与“已经”的区别，两版本都错误放行；T015 对“内部”与“外部”的区别，参考歧义保留，不把两版简单归入共同正确或共同错误。T003 的候选理由还把没有显示在窗口中的财报期间写进解释，虽然主判定与参考一致，也应作为理由过度推断记录。逐项更正归因见本地忽略目录中的 `corrected-attribution-diff.md`。

候选 T001、T013、T016 的中文理由本身指出日期、金额或否定关系与窗口矛盾，却输出 `supported`；这属于**语义上的判定与理由冲突**，现有确定性校验不会识别。T007、T014 属于**摘录出处校验失败**，不能算成候选语义正确或错误。不能通过忽略这两项提高候选比例；其中 T013 是双方共同错误，T001/T016 才是候选相对 baseline 的退化。

本次候选既未减少错误放行，也降低了输出接受数；因此**暂停将 candidate-v1 用于默认路径**。它仍作为未启用的实验版本保留，便于复核。一次配对诊断受关联窗口、代理标签和生成随机性限制；不能证明提示词一般效果。完整 16 项、逐项耗时、原始响应、确定性校验记录及细项对照在本地忽略目录，未进入 Git。

## 测试与依赖状态

此前 bundled Python 环境的全量发现为 255 项，其中 238 项通过、17 项因该解释器缺少 FastAPI/TestClient 而跳过；这不是 255 项同环境全通过。本轮使用仓库现有 `.local_data/venvs/sec-embedding/bin/python` 隔离环境补跑跳过项：

```bash
PYTHONPATH=src .local_data/venvs/sec-embedding/bin/python -m unittest tests.test_local_app.LocalAppTests -v
```

实际结果：`Ran 17 tests in 0.104s, OK`，0 skipped，退出码 0；另以 `discover -p test_local_app.py` 验证 18 项、0 skipped。该环境含 FastAPI 0.142.2、Starlette 1.7.0、httpx 0.28.1、Pydantic 2.13.5、Uvicorn 0.54.0，但缺 openpyxl；运行仅有 Starlette 关于 httpx 的弃用警告。系统 `python3` 3.12.4 缺 FastAPI 与 openpyxl。上述测试均未调用模型、SEC 或行情服务；此前 238 项与本轮 17 项不是同一次全量运行，不能合并宣称 255 项单次通过。

运行准备模式不会调用 Ollama；只有显式 `--run-model` 才会调用。旧 16 项诊断不能当作这个候选的未见测试。本轮不接入网页、不自动改写答案、不改变默认生成路径。17 项跳过测试已在既有隔离环境全部补跑完成；本轮暂停提示词优化和追加诊断调用，不自动启用 candidate-v1。本轮记录已完成，剩余仅人工标签确认与未来可选的统一全量测试，不构成本轮阻塞；本轮不追加调用或修改参考标签。
