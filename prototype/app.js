(() => {
  const app = document.querySelector('#app');
  const modal = document.querySelector('#modal');
  const modalBody = document.querySelector('#modal-body');
  const modalTitle = document.querySelector('#modal-title');
  const pageTitle = document.querySelector('#page-title');
  const pageEyebrow = document.querySelector('#page-eyebrow');
  const globalNotice = document.querySelector('#global-notice');
  const environmentLabel = document.querySelector('#environment-label');
  const sidebarState = document.querySelector('#sidebar-state');
  const mockLabel = '<span class="mock">● 演示数据 / Mock Data</span>';
  const supportedSymbols = new Set(['NVDA', 'AAPL', 'MSFT']);
  let currentView = 'sec-evidence';

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function setPageMeta(view, title) {
    const isRealEvidence = view === 'sec-evidence';
    const isResearchRecord = view === 'history';
    pageEyebrow.textContent = isRealEvidence ? 'SEC EVIDENCE SEARCH' : isResearchRecord ? 'SAVED RESEARCH RECORDS' : view === 'home' ? 'RESEARCH WORKSPACE' : view === 'process' ? 'DATA PREPARATION' : 'FOLLOW-UP MODULE';
    pageTitle.textContent = title;
    globalNotice.textContent = isRealEvidence
      ? '当前仅检索已保存的 SEC 文件证据，不生成 LLM 回答；其他演示页面仍为 Mock Data。'
      : isResearchRecord ? '当前读取本地已保存的 SEC 研究记录，不会重新检索或调用模型；事实内容尚未人工核验。'
      : '当前页面是离线原型，行情、财务事实和图表均为演示数据，不代表真实分析。';
    environmentLabel.innerHTML = isRealEvidence ? '本地离线 · <span>真实 SEC 语料</span>' : isResearchRecord ? '本地离线 · <span>已保存研究记录</span>' : '演示环境 · <span>Mock Data</span>';
    sidebarState.textContent = isRealEvidence ? '本地 SEC 证据检索' : isResearchRecord ? '本地 SEC 研究记录' : 'Prototype / Mock Data';
    document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === (view === 'process' || view === 'report' ? 'home' : view)));
  }

  function render(content, view = 'home', title = '搜索与分析') {
    currentView = view;
    setPageMeta(view, title);
    app.innerHTML = `<div class="page-view">${content}</div>`;
    window.scrollTo(0, 0);
  }

  function safeSecUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname === 'www.sec.gov' && !url.username && !url.password && (!url.port || url.port === '443') && url.pathname.startsWith('/Archives/') ? url.href : null;
    } catch (_) { return null; }
  }

  function evidenceCard(result) {
    const secUrl = safeSecUrl(result.source_url);
    const date = result.filing_date || result.accepted_at || '未提供';
    const sourceLabel = {
      both: '关键词 + 语义共同命中',
      bm25: '关键词检索命中',
      dense: '语义检索命中',
    }[result.retrieved_by] || '检索来源未标注';
    const auditValue = (value) => value === null || value === undefined || value === '' ? '未进入该路候选' : escapeHtml(value);
    const sourceLink = secUrl
      ? `<a href="${escapeHtml(secUrl)}" target="_blank" rel="noopener noreferrer">查看 SEC 原始文件 ↗</a>`
      : '<span class="muted">来源链接未通过校验</span>';
    return `<article class="card evidence-result" data-chunk-id="${escapeHtml(result.chunk_id || '')}">
      <div class="evidence-result-head"><span class="tag">第 ${escapeHtml(result.rank)} 名</span><strong>${escapeHtml(result.symbol)} · ${escapeHtml(result.company_name || '')}</strong><span class="muted">${escapeHtml(result.form)} · ${escapeHtml(date)}</span></div>
      <p class="evidence-section">章节：${escapeHtml(result.section_title || result.section || '未标注')}</p>
      <p class="evidence-preview">${escapeHtml(result.evidence_excerpt || '')}</p>
      <p class="evidence-source-tag">${sourceLabel}</p>
      <div class="evidence-source">${sourceLink}</div>
      <details class="evidence-technical"><summary>查看技术详情</summary><dl>
        <div><dt>BM25 rank</dt><dd>${auditValue(result.bm25_rank)}</dd></div>
        <div><dt>Dense rank</dt><dd>${auditValue(result.dense_rank)}</dd></div>
        <div><dt>RRF score</dt><dd>${auditValue(result.rrf_score)}</dd></div>
        <div><dt>CIK</dt><dd>${auditValue(result.cik)}</dd></div>
        <div><dt>Accession</dt><dd>${auditValue(result.accession_number)}</dd></div>
        <div><dt>Chunk ID</dt><dd>${auditValue(result.chunk_id)}</dd></div>
        <div><dt>Chunk index</dt><dd>${auditValue(result.chunk_index)}</dd></div>
        <div><dt>Section ID</dt><dd>${auditValue(result.section_id)}</dd></div>
        <div><dt>Corpus as-of</dt><dd>${auditValue(result.corpus_as_of)}</dd></div>
      </dl></details>
    </article>`;
  }

  function renderLocalAnswer(container, payload, evidenceRoot) {
    const element = (tag, className, content) => {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (content !== undefined) node.textContent = String(content);
      return node;
    };
    const citations = new Map((Array.isArray(payload.citations) ? payload.citations : []).map((item) => [item.evidence_id, item]));
    const card = element('section', 'panel local-answer');
    card.append(element('h2', '', '本地模型生成的中文回答'));
    const record = payload.research_record || {};
    const saveStatus = record.save_status || '未提供';
    const saveMessage = saveStatus === 'saved' ? '回答已保存为研究记录。' : `回答已生成，但研究记录${statusLabel(saveStatus) === '未提供' ? '保存状态未提供' : `保存${statusLabel(saveStatus)}`}。`;
    card.append(element('p', saveStatus === 'saved' ? 'notice' : 'notice', saveMessage));
    if (record.record_id) {
      const recordLink = element('button', 'button-link', '打开研究记录');
      recordLink.type = 'button';
      recordLink.addEventListener('click', () => researchRecordDetail(record.record_id));
      card.append(recordLink);
    }
    card.append(element('p', 'small muted', `模型：${payload.generation?.model || '未标注'} · 生成耗时：${payload.generation?.total_duration_ms ?? '未提供'} ms · 本地调用：${payload.generation?.local_model_calls ?? '未提供'} · 外部数据请求：无`));
    const addReferences = (parent, refs) => {
      (Array.isArray(refs) ? refs : []).forEach((ref) => {
        const citation = citations.get(ref);
        if (!citation) return;
        const button = element('button', 'answer-citation', `[${ref}]`);
        button.type = 'button';
        button.setAttribute('aria-label', `跳转到证据 ${ref}`);
        button.addEventListener('click', () => {
          const target = Array.from(evidenceRoot.querySelectorAll('.evidence-result'))
            .find((item) => item.dataset.chunkId === citation.chunk_id);
          if (!target) return;
          const group = target.closest('.more-evidence');
          if (group) group.open = true;
          target.classList.add('citation-highlight');
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
          window.setTimeout(() => target.classList.remove('citation-highlight'), 3000);
        });
        parent.append(button);
      });
    };
    const answer = payload.answer || {};
    if (payload.answer_status === 'evidence_insufficient') {
      card.append(element('p', 'answer-insufficient', '证据不足：当前 SEC 片段不足以支持可靠回答。'));
    } else if (payload.answer_status === 'completed') {
      const direct = element('p', 'answer-direct', answer.direct_answer?.text || '');
      addReferences(direct, answer.direct_answer?.evidence_ids);
      card.append(direct);
      if (Array.isArray(answer.key_points) && answer.key_points.length) {
        const list = element('ul', 'answer-points');
        answer.key_points.forEach((point) => {
          const item = element('li', '', point.text || '');
          addReferences(item, point.evidence_ids);
          list.append(item);
        });
        card.append(list);
      }
    } else {
      card.append(element('p', 'answer-insufficient', '本地模型没有返回可接受的回答。'));
    }
    if (Array.isArray(answer.limitations) && answer.limitations.length) {
      card.append(element('h3', '', '局限与不确定性'));
      const list = element('ul', 'answer-limitations');
      answer.limitations.forEach((item) => list.append(element('li', '', item)));
      card.append(list);
    }
    card.append(element('p', 'small muted', '本地模型生成，仅基于下方 SEC 证据，请自行核验。不构成投资建议。'));
    container.replaceChildren(card);
  }

  async function secEvidence() {
    render('<div class="panel"><h2>正在读取本地 SEC 语料…</h2><p class="muted">仅访问本机应用，不发起新的 SEC 或模型下载请求。</p></div>', 'sec-evidence', 'SEC 证据检索');
    try {
      const [healthResponse, securitiesResponse] = await Promise.all([fetch('/api/health'), fetch('/api/securities')]);
      if (currentView !== 'sec-evidence') return;
      if (!healthResponse.ok || !securitiesResponse.ok) throw new Error('本地检索服务不可用');
      const health = await healthResponse.json();
      const securitiesPayload = await securitiesResponse.json();
      const securities = Array.isArray(securitiesPayload) ? securitiesPayload : securitiesPayload.securities;
      if (!Array.isArray(securities) || !securities.length) throw new Error('没有可检索的 SEC 公司');
      const options = securities.map((security) => `<option value="${escapeHtml(security.symbol)}">${escapeHtml(security.symbol)} · ${escapeHtml(security.company_name)}</option>`).join('');
      const coverage = securities.map((security) => `<div class="coverage-item"><b>${escapeHtml(security.symbol)}</b><span>${escapeHtml(security.company_name)}</span><small>CIK ${escapeHtml(security.CIK || security.cik || '未提供')}</small><small>${escapeHtml(security.document_count)} 份文件 · ${escapeHtml(security.chunk_count)} 个片段 · ${escapeHtml((security.available_forms || []).join(' / '))}</small></div>`).join('');
      render(`<section class="panel evidence-intro"><span class="tag">真实本地数据 · SEC 证据检索</span><h2>在已保存的 SEC 财报中查找证据</h2><p class="muted">选择有语料的公司，输入英文或中文问题。检索结果来自 BM25 关键词检索、BGE 语义检索和固定 RRF 排序；只有主动点击后才尝试本地模型回答。</p>
        <div class="evidence-status">语料截止：${escapeHtml(health.corpus_as_of || '未提供')} · ${escapeHtml(health.document_count)} 份文件 · ${escapeHtml(Number(health.chunk_count).toLocaleString('en-US'))} 个片段 · 外部数据请求：无 · <span id="local-model-count">本次检索的 LLM 调用：0</span></div>
        <form id="sec-search-form" class="evidence-form"><label>公司<select name="symbol" required>${options}</select></label><label>表单<select name="form"><option value="">10-K + 10-Q</option><option value="10-K">仅 10-K</option><option value="10-Q">仅 10-Q</option></select></label><label class="question-field">SEC 财报问题（英文或中文）<input name="question" type="text" minlength="3" maxlength="1000" required placeholder="What risks could affect demand for the company's products?"></label><button class="primary" type="submit">检索真实证据</button></form>
        <p class="small muted">证据检索只读取本机文件；不会下载新 SEC 文件。${health.ollama_enabled ? '可在检索后主动调用本地 Ollama 生成中文回答。' : '本地模型回答未启用。'}</p></section>
        <details class="panel coverage-panel"><summary><span><b>当前真实语料覆盖</b><small>${escapeHtml(securities.length)} 家公司 · ${escapeHtml(health.document_count)} 份文件 · ${escapeHtml(Number(health.chunk_count).toLocaleString('en-US'))} 个片段</small></span><span class="coverage-toggle">查看覆盖公司</span></summary><p class="small muted">仅显示已建索引公司；能搜索证券不等于已有 RAG 语料。</p><div class="coverage-grid">${coverage}</div></details>
        <section id="sec-results" aria-live="polite"></section>`, 'sec-evidence', 'SEC 证据检索');
      globalNotice.textContent = health.ollama_enabled
        ? 'SEC 证据检索不会调用模型；点击生成按钮后才会调用本机 Ollama。其他演示页面仍为 Mock Data。'
        : '当前仅检索已保存的 SEC 文件证据；本地模型回答未启用。其他演示页面仍为 Mock Data。';
      document.querySelector('#sidebar-model-state').textContent = health.ollama_enabled ? '回答仅在点击后生成' : '本地模型回答未启用';
      document.querySelector('.coverage-panel').addEventListener('toggle', (event) => {
        event.currentTarget.querySelector('.coverage-toggle').textContent = event.currentTarget.open ? '收起覆盖公司' : '查看覆盖公司';
      });
      let searchGeneration = 0;
      document.querySelector('#sec-search-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const requestGeneration = ++searchGeneration;
        const form = event.currentTarget;
        const submit = form.querySelector('button[type="submit"]');
        const results = document.querySelector('#sec-results');
        const fields = new FormData(form);
        const searchRequest = { symbol: fields.get('symbol'), question: fields.get('question'), form: fields.get('form') || null, as_of: health.corpus_as_of, top_k: 10 };
        submit.disabled = true;
        document.querySelector('#local-model-count').textContent = '本次检索的 LLM 调用：0';
        results.innerHTML = '<div class="panel"><p>正在从本地索引检索…</p></div>';
        try {
          const response = await fetch('/api/sec/evidence-search', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(searchRequest) });
          if (!response.ok) throw new Error(response.status === 422 ? '请输入有效的问题和筛选条件。' : '检索失败；请检查本地服务和语料状态。');
          const payload = await response.json();
          if (requestGeneration !== searchGeneration) return;
          const hits = Array.isArray(payload.evidence) ? payload.evidence : [];
          if (payload.answer_status !== 'not_generated') throw new Error('服务未确认仅返回检索证据。');
          const firstHits = hits.slice(0, 3);
          const remainingHits = hits.slice(3);
          results.innerHTML = `<div class="section-title"><h2>检索结果</h2><span class="muted">${escapeHtml(hits.length)} 个证据片段 · 截止 ${escapeHtml(payload.filters?.as_of || health.corpus_as_of || '未提供')}</span></div>
            <div class="notice" id="evidence-boundary-notice">以下是 SEC 原文证据，不是问题答案；当前尚未调用 LLM。排名不代表结论正确，也不构成投资建议。点击 SEC 链接会访问外部 SEC 网站。</div>
            ${hits.length ? `<div class="evidence-list">${firstHits.map(evidenceCard).join('')}</div>${remainingHits.length ? `<details class="more-evidence"><summary>查看其余 ${escapeHtml(remainingHits.length)} 条证据</summary><div class="evidence-list">${remainingHits.map(evidenceCard).join('')}</div></details>` : ''}` : '<div class="panel"><p>此筛选条件下没有可用证据。请调整问题或表单；不会用模型常识补齐。</p></div>'}
            ${health.ollama_enabled && hits.length ? '<div class="answer-action"><button class="primary" type="button" id="generate-local-answer">生成中文回答（本地模型）</button><p class="small muted">需主动点击；回答只依据这次检索的 SEC 证据，不是投资建议。</p></div><section id="sec-answer" aria-live="polite"></section>' : ''}`;
          if (health.ollama_enabled && hits.length) {
            const button = document.querySelector('#generate-local-answer');
            const answerContainer = document.querySelector('#sec-answer');
            button.addEventListener('click', async () => {
              const answerGeneration = requestGeneration;
              button.disabled = true;
              document.querySelector('#evidence-boundary-notice').textContent = '以下仍是 SEC 原文证据，不是模型回答；已尝试本地模型生成。排名不代表结论正确，也不构成投资建议。点击 SEC 链接会访问外部 SEC 网站。';
              answerContainer.replaceChildren();
              const progress = document.createElement('p');
              progress.textContent = '本地模型正在阅读 SEC 证据，首次运行可能需要较长时间……';
              answerContainer.append(progress);
              let reportedCalls = null;
              try {
                const answerResponse = await fetch('/api/sec/answer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(searchRequest) });
                if (!answerResponse.ok) {
                  const failure = await answerResponse.json().catch(() => ({}));
                  if (Number.isInteger(failure.generation?.llm_calls)) reportedCalls = failure.generation.llm_calls;
                  const safeDetails = new Set([
                    '所选本地模型尚未安装；SEC 证据检索仍可使用。',
                    'Ollama 本地服务不可用；SEC 证据检索仍可使用。',
                    '本地模型响应超时；SEC 证据检索仍可使用。',
                    '本地模型输出未通过证据校验；SEC 证据检索仍可使用。',
                    '本地模型响应无效；SEC 证据检索仍可使用。',
                  ]);
                  throw new Error(safeDetails.has(failure.detail) ? failure.detail : '本地模型暂不可用或回答未通过证据校验；上方 SEC 证据仍可查看。');
                }
                const answerPayload = await answerResponse.json();
                if (answerGeneration !== searchGeneration) return;
                renderLocalAnswer(answerContainer, answerPayload, results);
                document.querySelector('#local-model-count').textContent = `本次检索的 LLM 调用：${answerPayload.generation?.llm_calls ?? '未提供'}`;
              } catch (error) {
                if (answerGeneration !== searchGeneration) return;
                const notice = document.createElement('p');
                notice.className = 'notice';
                notice.setAttribute('role', 'alert');
                notice.textContent = error.message;
                answerContainer.replaceChildren(notice);
                document.querySelector('#local-model-count').textContent = Number.isInteger(reportedCalls)
                  ? `本次检索的 LLM 调用：${reportedCalls}` : '本次检索的 LLM 调用：失败后状态未确认';
              } finally { button.disabled = false; }
            });
          }
        } catch (error) {
          results.innerHTML = `<div class="notice" role="alert">${escapeHtml(error.message)}</div>`;
        } finally { submit.disabled = false; }
      });
    } catch (_) {
      if (currentView !== 'sec-evidence') return;
      render('<div class="panel"><h2>本地 SEC 检索暂不可用</h2><p class="muted">请先按 README 启动本地服务，并确认离线语料、索引和模型缓存可读取。此页面不会自动访问 SEC。</p></div>', 'sec-evidence', 'SEC 证据检索');
    }
  }

  function home() {
    render(`
      <section class="hero">
        <div class="panel hero-panel">
          <span class="tag">P0 原型闭环</span>
          <h2>把行情与 SEC 证据放在同一条研究路径里</h2>
          <p class="lead">搜索股票，查看已保存日线、财务事实、来源和数据状态。${mockLabel}</p>
          <div class="search">
            <input id="query" value="NVDA" aria-label="股票代码或公司名称" maxlength="40" autocomplete="off">
            <button class="primary" id="analyze">开始分析</button>
          </div>
          <p class="small muted">演示选项：NVDA · AAPL · MSFT。当前不连接真实 API，不提供投资建议。</p>
        </div>
        <div class="panel">
          <div class="section-title"><h3>当前样例</h3><span class="data-state"><span class="status-dot"></span>离线快照</span></div>
          <div class="status ok"><b>NVDA · 研究快照</b><br><span class="small muted">日线已保存 · SEC 文件可查看</span></div>
          <div class="status warn"><b>新闻时间线：接口预留</b><br><span class="small muted">尚未接入真实新闻数据</span></div>
          <p class="small muted">本轮重点：已保存日线、可追溯事实、可展开证据。</p>
        </div>
      </section>
      <div class="section-title"><h2>本轮验证重点</h2><span class="muted">结论、证据与数据状态优先</span></div>
      <div class="grid">
        <div class="card"><h3>已保存日线</h3><p class="muted">查看 OHLCV、日期、来源和延迟状态。</p></div>
        <div class="card"><h3>可追溯事实</h3><p class="muted">每个数字展示单位、期间和文件来源。</p></div>
        <div class="card"><h3>可展开证据</h3><p class="muted">先读摘要，再查看事实与风险限制。</p></div>
      </div>`, 'home', '搜索与分析');
    document.querySelector('#analyze').addEventListener('click', () => process(document.querySelector('#query').value));
    document.querySelector('#query').addEventListener('keydown', (event) => { if (event.key === 'Enter') process(event.target.value); });
  }

  function process(rawSymbol) {
    const normalized = String(rawSymbol || '').trim().toUpperCase().replace(/[^A-Z0-9 .-]/g, '');
    const symbol = normalized || 'NVDA';
    const displaySymbol = escapeHtml(symbol);
    render(`
      <div class="panel process-panel">
        <span class="tag">数据处理步骤</span>
        <h2>${displaySymbol} 研究准备</h2>
        <p class="muted">${mockLabel} 离线演示步骤，不代表真实请求或后台任务已经执行。</p>
        ${['读取已保存行情', '获取 SEC 文件', '提取财务事实', '检查时间和来源', '生成摘要', '准备导出'].map((step) => `<div class="status ok">✓ ${step}</div>`).join('')}
        <div class="actions"><button class="primary" id="report">查看演示报告</button><button data-view="home">返回搜索</button></div>
      </div>`, 'process', '数据处理');
    document.querySelector('#report').addEventListener('click', report);
  }

  function chartMarkup() {
    return `<div class="chart" aria-label="NVDA 演示日 K 线图">
      <svg viewBox="0 0 640 210" role="img" aria-labelledby="chart-title chart-desc">
        <title id="chart-title">NVDA Mock Data 日 K 线</title><desc id="chart-desc">固定 synthetic 数据，仅用于离线原型交互演示</desc>
        <line class="gridline" x1="20" y1="35" x2="620" y2="35"/><line class="gridline" x1="20" y1="95" x2="620" y2="95"/><line class="gridline" x1="20" y1="155" x2="620" y2="155"/>
        <g class="candle-up"><line x1="80" y1="88" x2="80" y2="145" stroke-width="2"/><rect x="71" y="104" width="18" height="28"/><line x1="190" y1="62" x2="190" y2="116" stroke-width="2"/><rect x="181" y="76" width="18" height="26"/><line x1="300" y1="79" x2="300" y2="137" stroke-width="2"/><rect x="291" y="92" width="18" height="29"/><line x1="410" y1="39" x2="410" y2="99" stroke-width="2"/><rect x="401" y="53" width="18" height="29"/><line x1="520" y1="31" x2="520" y2="87" stroke-width="2"/><rect x="511" y="45" width="18" height="25"/></g>
        <g class="candle-down"><line x1="135" y1="71" x2="135" y2="127" stroke-width="2"/><rect x="126" y="82" width="18" height="29"/><line x1="245" y1="70" x2="245" y2="126" stroke-width="2"/><rect x="236" y="82" width="18" height="28"/><line x1="355" y1="51" x2="355" y2="105" stroke-width="2"/><rect x="346" y="64" width="18" height="27"/><line x1="465" y1="39" x2="465" y2="88" stroke-width="2"/><rect x="456" y="48" width="18" height="25"/><line x1="575" y1="28" x2="575" y2="77" stroke-width="2"/><rect x="566" y="40" width="18" height="23"/></g>
        <g><text x="58" y="194">09/12</text><text x="168" y="194">09/14</text><text x="278" y="194">09/16</text><text x="388" y="194">09/17</text><text x="498" y="194">09/18</text></g>
      </svg></div>`;
  }

  function factsMarkup() {
    return `<div class="table-wrap"><table><thead><tr><th>财务事实</th><th>数值</th><th>报告期 / 单位</th><th>文件 / 公开时间</th><th>来源</th></tr></thead><tbody>
      <tr><td>Revenue</td><td><b>$130.5B</b></td><td>FY2025 · USD<br><span class="small muted">口径：年度合并</span></td><td>10-K<br><span class="small muted">2025-02-26</span></td><td><button class="button-link" data-source="SEC 10-K">查看来源</button></td></tr>
      <tr><td>Net income</td><td><b>$72.9B</b></td><td>FY2025 · USD<br><span class="small muted">口径：年度合并</span></td><td>Company Facts<br><span class="small muted">2025-02-26</span></td><td><button class="button-link" data-source="SEC Company Facts">查看来源</button></td></tr>
    </tbody></table></div>`;
  }

  function report() {
    render(`<div class="report-header"><div><span class="tag">NVDA · 单股研究</span><h2>研究快照与证据摘要</h2><p class="subhead">NVIDIA Corporation · NASDAQ</p></div><span class="mock">● Mock Data</span></div>
      <div class="notice">数据状态：日线为已保存演示快照；行情截止 2026-09-18，原型仅展示延迟说明。SEC 事实为模拟展示，真实 RAG 尚未实现。</div>
      <div class="two" style="margin-top:18px"><div class="card"><div class="section-title"><h3>日线行情概览</h3><span class="data-state"><span class="status-dot"></span>已保存快照</span></div><div class="grid"><div><span class="metric-label">最新收盘价</span><div class="metric">$178.24</div></div><div><span class="metric-label">当日涨跌</span><div class="metric">+1.8%</div></div><div><span class="metric-label">成交量</span><div class="metric">42.1M</div></div></div><p class="small muted">数据时间：2026-09-18 16:00 ET · 币种：USD · 复权：未复权 · 来源状态：Mock Data</p><h3 style="margin-top:24px">简化 K 线预览</h3>${chartMarkup()}<p class="small mock">固定 synthetic 日 K 示意，不是真实 NVDA 行情；日期、OHLC、成交量仅用于交互演示。</p></div>
        <div class="card"><h3>简短摘要</h3><div class="summary-list"><p><b>事实：</b>演示快照包含收入与净利润记录。</p><p><b>计算：</b>收盘价和涨跌幅来自保存的日线字段。</p><p><b>推断：</b>仅提供需要进一步核验的研究线索。</p><p><b>风险与缺失：</b>新闻未接入，不能完成事件归因；缺失值不会填 0。</p></div><button class="primary" id="evidence" style="margin-top:18px">展开证据</button><div class="evidence-box"><b>数据缺失</b><p class="small muted">新闻时间线尚未接入，因此事件原因分析证据不足。仍可查看日线、SEC 模拟事实和来源卡片。</p></div></div></div>
      <div class="card" style="margin-top:18px"><div class="section-title"><h3>SEC 文件与财务事实</h3><span class="mock">模拟来源 · 真实 RAG 尚未实现</span></div>${factsMarkup()}<div class="actions"><button id="excel">预览 Excel 导出</button><button id="runlog">查看运行记录</button><button>加入自选股（后续功能）</button></div><p class="small muted">报告已生成 ≠ 邮件已发送。邮件属于 P1，当前默认关闭。</p></div>`, 'report', '研究报告');
    document.querySelector('#evidence').addEventListener('click', () => openModal('证据详情', '<p><b>事实</b>：财务数字来自模拟 SEC 文件卡片。</p><p><b>计算</b>：涨跌幅由保存的开收盘字段确定性计算。</p><p><b>推断</b>：不能替代投资判断。</p><p><b>风险与缺失</b>：新闻、完整 RAG 和多 Agent 尚未实现；缺失数据不会填 0。</p>'));
    document.querySelector('#excel').addEventListener('click', excel);
    document.querySelector('#runlog').addEventListener('click', runlog);
    document.querySelectorAll('[data-source]').forEach((button) => button.addEventListener('click', () => openModal('来源卡片', `<p><b>${escapeHtml(button.dataset.source)}</b></p><p>官方来源位置和公开时间将在真实数据接入后保存。当前为模拟来源，不能打开真实文件。</p><p class="mock">Mock Data · 真实 SEC 引用尚未接入</p>`)));
  }

  function excel() { openModal('Excel 导出预览', `<p class="mock">Mock Data · 当前不会真正下载文件</p><p>真实导出只能读取已保存快照，数字不能由 LLM 临时生成。</p><ul>${['Summary', 'Daily OHLCV', 'SEC Facts', 'Sources', 'Data Quality', 'Run Log'].map((sheet) => `<li>${sheet}</li>`).join('')}</ul><p class="muted">每个工作表将保存来源、时间、单位、口径、延迟和缺失状态。</p>`); }

  function runlog() { openModal('运行记录（Prototype / Mock）', `<table><tbody>${[['run_id', 'demo-run-nvda-001'], ['symbol', 'NVDA'], ['started_at', '2026-09-18T20:00:00Z'], ['completed_at', '2026-09-18T20:00:03Z'], ['data_as_of', '2026-09-18T20:00:00Z'], ['market_source', 'saved daily snapshot (Mock)'], ['SEC source', 'SEC fixture (Mock)'], ['task_status', 'completed (prototype)'], ['missing_data', 'news timeline'], ['warnings', 'not investment advice; RAG not implemented'], ['export_status', 'preview only; not downloaded']].map(([key, value]) => `<tr><th>${key}</th><td>${value}</td></tr>`).join('')}</tbody></table>`); }

  function secondary(view) {
    if (view === 'history') return researchRecords();
    const titles = { watchlist: '我的自选股', daily: '收盘报告' };
    render(`<div class="panel placeholder"><span class="tag">后续功能</span><h2>${titles[view]}</h2><p class="muted">该页面保留用于范围展示，当前不抢占 P0 验证路径。</p><div class="notice">待实现：分钟级监测、条件式邮件投递、5/20 交易日复盘和真实数据连接。</div><div class="actions"><button class="primary" data-view="home">回到搜索首页</button></div></div>`, view, titles[view]);
  }

  function statusLabel(value) {
    const labels = { saved: '已保存', completed: '已完成', pending: '待处理', failed: '失败', not_saved: '未保存', reviewed: '已人工核验', unreviewed: '尚未人工核验', pending_human_review: '待人工复核' };
    return labels[value] || (value ? String(value) : '未提供');
  }

  function recordEvidenceCard(item, index) {
    const evidenceId = item.evidence_id || item.id || `evidence-${index + 1}`;
    const source = safeSecUrl(item.source_url);
    return `<article class="card evidence-result record-evidence" data-evidence-id="${escapeHtml(evidenceId)}">
      <div class="evidence-result-head"><span class="tag">证据 ${escapeHtml(evidenceId)}</span><strong>${escapeHtml(item.symbol || '')} · ${escapeHtml(item.form || 'SEC')}</strong><span class="muted">${escapeHtml(item.filing_date || item.published_at || '日期未提供')}</span></div>
      <p class="evidence-section">${escapeHtml(item.section_title || item.section || item.location || '来源定位未提供')}</p>
      <p class="evidence-preview">${escapeHtml(item.evidence_excerpt || item.text || item.excerpt || '原文片段未提供')}</p>
      <p class="small muted">来源：${source ? `<a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">SEC 原始文件</a>` : '链接未通过校验'} · 截止时间：${escapeHtml(item.data_as_of || item.corpus_as_of || '未提供')}</p>
    </article>`;
  }

  function recordStatus(record) {
    return `<span class="record-status">保存：${escapeHtml(statusLabel(record.save_status))} · 审阅：${escapeHtml(statusLabel(record.review_status || 'unreviewed'))}</span>`;
  }

  async function researchRecords() {
    render('<div class="panel"><h2>正在读取研究记录…</h2><p class="muted">仅读取本地已保存记录，不会重新检索或调用模型。</p></div>', 'history', '研究记录');
    let limit = 10;
    let offset = 0;
    let symbol = '';
    const load = async () => {
      const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      if (symbol) query.set('symbol', symbol);
      const response = await fetch(`/api/research-records?${query.toString()}`);
      if (!response.ok) throw new Error('研究记录暂时不可用。');
      const payload = await response.json();
      const items = Array.isArray(payload.items) ? payload.items : [];
      const list = items.map((record) => `<button type="button" class="record-row" data-record-id="${escapeHtml(record.record_id)}"><span><b>${escapeHtml(record.symbol || '未知证券')}</b><span class="record-question">${escapeHtml(record.question || '问题未提供')}</span></span><span>${escapeHtml(record.created_at || '时间未提供')}<br>${recordStatus(record)}</span></button>`).join('');
      render(`<section class="panel records-panel"><span class="tag">本地 SEC 研究记录</span><h2>研究记录</h2><p class="muted">这里仅展示已保存的研究回答与证据，不是 5/20 个交易日历史复盘。<br><b>事实内容尚未人工核验。</b></p><form id="records-filter" class="records-filter"><label>股票筛选<input name="symbol" value="${escapeHtml(symbol)}" maxlength="12" placeholder="例如 NVDA"></label><button class="primary" type="submit">筛选</button></form>${items.length ? `<div class="record-list">${list}</div>` : '<div class="notice">没有找到已保存的研究记录；不会自动重新生成。</div>'}<div class="records-pagination"><button type="button" id="records-prev" ${offset <= 0 ? 'disabled' : ''}>上一页</button><span>第 ${Math.floor(offset / limit) + 1} 页 · 共 ${escapeHtml(payload.total ?? items.length)} 条</span><button type="button" id="records-next" ${offset + limit >= Number(payload.total || 0) ? 'disabled' : ''}>下一页</button></div></section>`, 'history', '研究记录');
      document.querySelector('#records-filter').addEventListener('submit', (event) => { event.preventDefault(); symbol = new FormData(event.currentTarget).get('symbol').trim().toUpperCase(); offset = 0; load(); });
      document.querySelector('#records-prev').addEventListener('click', () => { offset = Math.max(0, offset - limit); load(); });
      document.querySelector('#records-next').addEventListener('click', () => { offset += limit; load(); });
      document.querySelectorAll('.record-row').forEach((button) => button.addEventListener('click', () => researchRecordDetail(button.dataset.recordId)));
    };
    try { await load(); } catch (_) { render('<div class="panel"><h2>研究记录不可用</h2><p class="muted">无法读取本地保存记录；不会自动重新生成回答。</p></div>', 'history', '研究记录'); }
  }

  async function researchRecordDetail(recordId) {
    render('<div class="panel"><h2>正在读取研究记录…</h2><p class="muted">不会重新检索或调用模型。</p></div>', 'history', '研究记录详情');
    try {
      const response = await fetch(`/api/research-records/${encodeURIComponent(recordId)}`);
      if (!response.ok) throw new Error('记录不存在或读取失败。');
      const record = await response.json();
      const evidence = Array.isArray(record.evidence) ? record.evidence : [];
      const citations = Array.isArray(record.citations) ? record.citations : [];
      const answer = record.answer && typeof record.answer === 'object' ? record.answer : {};
      const answerText = answer.direct_answer?.text || answer.text || '未保存可展示的回答。';
      const citationButtons = (answer.direct_answer?.evidence_ids || []).map((id) => `<button type="button" class="record-citation" data-evidence-target="${escapeHtml(id)}">[${escapeHtml(id)}]</button>`).join('');
      const keyPoints = Array.isArray(answer.key_points) ? answer.key_points : [];
      const pointMarkup = keyPoints.map((point) => `<li>${escapeHtml(point.text || point)} ${(point.evidence_ids || []).map((id) => `<button type="button" class="record-citation" data-evidence-target="${escapeHtml(id)}">[${escapeHtml(id)}]</button>`).join('')}</li>`).join('');
      render(`<section class="panel record-detail"><div class="section-title"><div><span class="tag">${escapeHtml(record.symbol || '未知证券')} · 研究记录</span><h2>${escapeHtml(record.question || '问题未提供')}</h2></div><button type="button" id="records-back">返回列表</button></div><p class="muted">记录 ID：${escapeHtml(record.record_id || recordId)} · 创建时间：${escapeHtml(record.created_at || '未提供')}</p><div class="notice"><b>事实内容尚未人工核验。</b> ${recordStatus(record)} · 数据截止：${escapeHtml(record.data_as_of || record.filters?.as_of || '未提供')}</div><h3>当时回答</h3><p class="record-answer">${escapeHtml(answerText)} ${citationButtons}</p>${pointMarkup ? `<h3>关键要点</h3><ul>${pointMarkup}</ul>` : ''}<h3>保存证据（${escapeHtml(evidence.length)} 条）</h3><div class="evidence-list">${evidence.length ? evidence.map(recordEvidenceCard).join('') : '<div class="notice">该记录没有保存证据，无法验证回答。</div>'}</div></section>`, 'history', '研究记录详情');
      document.querySelector('#records-back').addEventListener('click', researchRecords);
      document.querySelectorAll('.record-citation').forEach((button) => button.addEventListener('click', () => { const target = Array.from(document.querySelectorAll('[data-evidence-id]')).find((item) => item.dataset.evidenceId === button.dataset.evidenceTarget); if (target) { target.scrollIntoView({ behavior: 'smooth', block: 'center' }); target.classList.add('citation-highlight'); window.setTimeout(() => target.classList.remove('citation-highlight'), 3000); } }));
    } catch (_) { render('<div class="panel"><h2>研究记录损坏或不存在</h2><p class="muted">无法展示这条记录；不会自动重新生成。</p><button class="primary" id="records-back">返回研究记录</button></div>', 'history', '研究记录'); document.querySelector('#records-back').addEventListener('click', researchRecords); }
  }

  function openModal(modalHeading, content) { modalTitle.textContent = modalHeading; modalBody.innerHTML = content; modal.classList.add('open'); modal.setAttribute('aria-hidden', 'false'); modal.querySelector('.close').focus(); }
  function closeModal() { modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true'); }

  document.addEventListener('click', (event) => { const view = event.target.closest('[data-view]')?.dataset.view; if (!view) return; if (view === 'sec-evidence') secEvidence(); else if (view === 'home') home(); else secondary(view); });
  modal.querySelector('.close').addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && modal.classList.contains('open')) closeModal(); });
  secEvidence();
})();

// Keep the shell title aligned with the active prototype view.
document.addEventListener('click', function (event) {
  var view = event.target.closest('[data-view]')?.dataset.view;
  var titles = { 'sec-evidence': 'SEC 证据检索', home: '演示研究', watchlist: '我的自选股', daily: '收盘报告', history: '研究记录' };
  if (view && titles[view]) {
    var heading = document.querySelector('.topbar h1');
    if (heading) heading.textContent = titles[view];
    document.querySelectorAll('nav button').forEach(function (button) {
      button.classList.toggle('active', button.dataset.view === view);
    });
  }
});
