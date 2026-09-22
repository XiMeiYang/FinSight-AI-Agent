(() => {
  const app = document.querySelector('#app');
  const modal = document.querySelector('#modal');
  const modalBody = document.querySelector('#modal-body');
  const modalTitle = document.querySelector('#modal-title');
  const pageTitle = document.querySelector('#page-title');
  const pageEyebrow = document.querySelector('#page-eyebrow');
  const mockLabel = '<span class="mock">● 演示数据 / Mock Data</span>';
  const supportedSymbols = new Set(['NVDA', 'AAPL', 'MSFT']);

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function setPageMeta(view, title) {
    pageEyebrow.textContent = view === 'home' ? 'RESEARCH WORKSPACE' : view === 'process' ? 'DATA PREPARATION' : 'FOLLOW-UP MODULE';
    pageTitle.textContent = title;
    document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === (view === 'process' || view === 'report' ? 'home' : view)));
  }

  function render(content, view = 'home', title = '搜索与分析') {
    setPageMeta(view, title);
    app.innerHTML = `<div class="page-view">${content}</div>`;
    window.scrollTo(0, 0);
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
    const titles = { watchlist: '我的自选股', daily: '收盘报告', history: '历史复盘' };
    render(`<div class="panel placeholder"><span class="tag">后续功能</span><h2>${titles[view]}</h2><p class="muted">该页面保留用于范围展示，当前不抢占 P0 验证路径。</p><div class="notice">待实现：分钟级监测、条件式邮件投递、5/20 交易日复盘和真实数据连接。</div><div class="actions"><button class="primary" data-view="home">回到搜索首页</button></div></div>`, view, titles[view]);
  }

  function openModal(modalHeading, content) { modalTitle.textContent = modalHeading; modalBody.innerHTML = content; modal.classList.add('open'); modal.setAttribute('aria-hidden', 'false'); modal.querySelector('.close').focus(); }
  function closeModal() { modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true'); }

  document.addEventListener('click', (event) => { const view = event.target.dataset.view; if (!view) return; if (view === 'home') home(); else secondary(view); });
  modal.querySelector('.close').addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && modal.classList.contains('open')) closeModal(); });
  home();
})();

// Keep the shell title aligned with the active prototype view.
document.addEventListener('click', function (event) {
  var view = event.target && event.target.dataset ? event.target.dataset.view : null;
  var titles = { home: '搜索与即时分析', watchlist: '我的自选股', daily: '收盘报告', history: '历史复盘' };
  if (view && titles[view]) {
    var heading = document.querySelector('.topbar h1');
    if (heading) heading.textContent = titles[view];
    document.querySelectorAll('nav button').forEach(function (button) {
      button.classList.toggle('active', button.dataset.view === view);
    });
  }
});
