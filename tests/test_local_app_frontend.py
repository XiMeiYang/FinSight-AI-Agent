"""Synthetic browser-shell contract checks without SEC data or a network."""

from pathlib import Path
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "prototype" / "app.js"


class LocalAppFrontendTests(unittest.TestCase):
    def test_evidence_layout_and_escaping(self):
        script = r"""
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
let submitHandler;
const simple = () => ({innerHTML: '', textContent: '', classList: {toggle(){}, add(){}, remove(){}, contains(){return false;}}, setAttribute(){}, addEventListener(){}, focus(){}, querySelector(){return simple();}});
const app = simple();
const results = simple();
const form = simple();
form.addEventListener = (event, handler) => {if (event === 'submit') submitHandler = handler;};
form.querySelector = () => ({disabled: false});
const modal = simple();
const nodes = {'#app': app, '#modal': modal, '#modal-body': simple(), '#modal-title': simple(), '#page-title': simple(), '#page-eyebrow': simple(), '#global-notice': simple(), '#environment-label': simple(), '#sidebar-state': simple(), '#sec-search-form': form, '#sec-results': results};
const document = {querySelector: key => nodes[key] || simple(), querySelectorAll: () => [], addEventListener(){}};
const bad = '<img src=x onerror=alert(1)>';
const evidence = Array.from({length: 10}, (_, i) => ({
  rank: i + 1, symbol: 'NVDA', company_name: bad, form: '10-K', filing_date: '2026-01-01',
  section_title: bad, evidence_excerpt: bad, source_url: i === 0 ? 'https://www.sec.gov.evil/Archives/evil' : 'https://www.sec.gov/Archives/test.htm',
  retrieved_by: i === 0 ? 'both' : i === 1 ? 'bm25' : 'dense', bm25_rank: i + 1, dense_rank: i + 2,
  rrf_score: 0.03, cik: bad, accession_number: bad, chunk_id: bad, chunk_index: i, section_id: bad, corpus_as_of: '2026-09-18'
}));
let calls = 0;
const fetch = async (url, opts) => {
  calls++;
  if (url === '/api/health') return {ok: true, json: async () => ({corpus_as_of: '2026-09-18', document_count: 10, chunk_count: 2003})};
  if (url === '/api/securities') return {ok: true, json: async () => ({securities: [{symbol: 'NVDA', company_name: bad, CIK: '0001', document_count: 10, chunk_count: 2003, available_forms: ['10-K', '10-Q']}]})};
  assert.strictEqual(url, '/api/sec/evidence-search');
  assert.strictEqual(JSON.parse(opts.body).top_k, 10);
  return {ok: true, json: async () => ({answer_status: 'not_generated', evidence, filters: {as_of: '2026-09-18'}})};
};
class FormData {get(key){return {symbol:'NVDA', question:'What risks could affect demand?', form:''}[key];}}
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {document, window: {scrollTo(){}}, URL, FormData, fetch, console});
setTimeout(async () => {
  assert.ok(submitHandler);
  assert.match(app.innerHTML, /<details class="panel coverage-panel">/);
  assert.match(app.innerHTML, /1 家公司 · 10 份文件 · 2,003 个片段/);
  assert.ok(!app.innerHTML.includes(bad));
  await submitHandler({preventDefault(){}, currentTarget: form});
  const html = results.innerHTML;
  const split = html.indexOf('<details class="more-evidence">');
  assert.ok(split > 0);
  assert.strictEqual((html.slice(0, split).match(/class="card evidence-result"/g) || []).length, 3);
  assert.strictEqual((html.slice(split).match(/class="card evidence-result"/g) || []).length, 7);
  assert.match(html, /查看其余 7 条证据/);
  assert.match(html, /查看技术详情/);
  assert.match(html, /BM25 rank/);
  assert.match(html, /Dense rank/);
  assert.match(html, /RRF score/);
  assert.match(html, /关键词 \+ 语义共同命中/);
  assert.match(html, /关键词检索命中/);
  assert.match(html, /语义检索命中/);
  assert.match(html, /不是问题答案/);
  assert.ok(!html.includes(bad));
  assert.ok(html.includes('&lt;img'));
  assert.ok(!html.includes('href="https://www.sec.gov.evil'));
  assert.ok(html.includes('href="https://www.sec.gov/Archives/test.htm"'));
  assert.strictEqual(calls, 3);
  process.stdout.write('frontend synthetic checks passed\n');
}, 0);
"""
        result = subprocess.run(
            ["node", "-e", script, str(APP_JS)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "frontend synthetic checks passed")


if __name__ == "__main__":
    unittest.main()
