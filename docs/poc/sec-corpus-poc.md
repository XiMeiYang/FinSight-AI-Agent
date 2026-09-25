# 多公司 SEC 语料 PoC

目标公司为 NVDA、AMD、INTC、AVGO、QCOM。候选规则只选择精确 `10-K` 和 `10-Q`，每家公司最多 5 份 10-K、15 份 10-Q；修订表单不会被默认混入。CIK 来自 SEC ticker mapping，不硬编码。

本轮已生成候选清单与受控下载器已实现，但仅有 NVDA 的本地 submissions，可识别 25 份候选并选出 5 份 10-K、15 份 10-Q；其余四家公司仅能确认 ticker mapping，候选 submissions 数量为 0。由于 `FINSIGHT_SEC_USER_AGENT` 未配置，本轮没有执行网络请求，也没有下载或提交 SEC 文件。

`SecurityCatalog` 负责 ticker/公司名搜索与唯一解析；`rag_coverage` 单独报告 `not_built`、`available` 等语料覆盖状态，证券可搜索不等于已有 RAG 语料。后续联网构建必须在用户确认候选统计、限额和输出目录后显式使用 `--network`，并保留请求审计和总大小上限。

## 两阶段下载边界

第一阶段使用 `--candidate-only` 生成 manifest；第二阶段必须显式传入已审阅的 `--candidate-manifest` 并使用 `--network`。下载器复用 `SECClient`，只接受 SEC Archives primary document，保存 raw、metadata、document、chunks 和 manifests，并记录请求/重试/下载大小。缺少 `FINSIGHT_SEC_USER_AGENT` 时在任何请求前失败。本轮测试只使用 synthetic fixture 和 mock/零网络路径，未执行真实下载。

### 最后阻断修复

Candidate row 的 `ticker` 在下载保存 metadata 时显式转换为标准化 `symbol`，再交给 `build_sec_ingestion`；不会放宽 ingestion 的缺失身份校验。`--network --refresh-metadata` 只补齐缺失 submissions 并重新生成候选清单，不下载正文。正文下载必须使用带 ticker mapping 证明、截止时间和数量预算的已审阅 manifest。
