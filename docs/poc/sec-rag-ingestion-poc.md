# SEC RAG ingestion PoC

本轮实现离线 SEC HTML/XML 正文清洗、章节识别和确定性字符分块。未实现 embedding、向量数据库、LLM、Agent 或在线下载。

解析会移除 script/style/noscript 等不可信内容，保留段落、数字、单位和标题。分块目标约 2,000 字符、重叠 250 字符，输出包含 SHA-256 与引用定位信息。

当前 `.local_data/sec` 没有可确认的 10-K/10-Q 正文；已有文件主要是 submissions、Company Facts 和 ticker mapping，另有一份 8-K XML 文件。真实 NVDA filing 分块未执行，synthetic 测试已覆盖。
