"""Synthetic browser-shell contract checks without SEC data or a network."""

from pathlib import Path
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "prototype" / "app.js"
INDEX_HTML = APP_JS.with_name("index.html")


class LocalAppFrontendTests(unittest.TestCase):
    def test_html_versions_updated_static_assets(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('app.js?v=local-ollama-rag-20261008', html)
        self.assertIn('styles.css?v=local-ollama-rag-20261008', html)

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

    def test_local_answer_click_is_opt_in_escaped_and_citation_opens_evidence(self):
        script = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
let submitHandler, answerHandler;
const node = () => ({innerHTML: '', textContent: '', children: [], dataset: {}, listeners: {},
  classList: {toggle(){}, add(value){this[value]=true;}, remove(value){this[value]=false;}},
  append(...items){this.children.push(...items);}, replaceChildren(...items){this.children=items;},
  addEventListener(type, handler){this.listeners[type]=handler;}, setAttribute(){},
  querySelector(){return node();}, querySelectorAll(){return [];}, closest(){return null;}, scrollIntoView(){this.scrolled=true;}});
const app=node(), results=node(), form=node(), answerButton=node(), answerContainer=node(), coverage=node();
form.addEventListener=(type, handler)=>{if(type==='submit') submitHandler=handler;};
form.querySelector=()=>node();
answerButton.addEventListener=(type, handler)=>{if(type==='click') answerHandler=handler;};
const more=node(), evidenceCard=node(); evidenceCard.dataset.chunkId='chunk-1';
evidenceCard.closest=()=>more; results.querySelectorAll=()=>[evidenceCard];
const localModelCount=node();
const nodes={'#app':app,'#sec-search-form':form,'#sec-results':results,'#generate-local-answer':answerButton,'#sec-answer':answerContainer,'.coverage-panel':coverage,'#local-model-count':localModelCount};
const document={querySelector:key=>nodes[key]||node(), querySelectorAll:()=>[], addEventListener(){}, createElement:()=>node()};
const malicious='<img src=x onerror=alert(1)>';
let answerCalls=0, searchCalls=0, failAnswer=false;
const fetch=async (url,opts)=>{
 if(url==='/api/health')return {ok:true,json:async()=>({corpus_as_of:'2026-09-18',document_count:10,chunk_count:2003,ollama_enabled:true})};
 if(url==='/api/securities')return {ok:true,json:async()=>({securities:[{symbol:'NVDA',company_name:'NVIDIA',document_count:2,chunk_count:10,available_forms:['10-K','10-Q']}]})};
 if(url==='/api/sec/evidence-search'){searchCalls++;return {ok:true,json:async()=>({answer_status:'not_generated',evidence:[{rank:1,chunk_id:'chunk-1',symbol:'NVDA',company_name:'NVIDIA',form:'10-K',filing_date:'2026-01-01',evidence_excerpt:'Synthetic complete sentence.',source_url:'https://www.sec.gov/Archives/synthetic.htm'}]})};}
 if(url==='/api/sec/answer'){answerCalls++;assert.strictEqual(JSON.parse(opts.body).top_k,10);if(failAnswer)return {ok:false,status:503,json:async()=>({detail:'本地模型暂不可用；证据仍可查看。',generation:{llm_calls:0}})};return {ok:true,json:async()=>({answer_status:'completed',model_calls:1,generation:{model:'synthetic',local_model_calls:1,llm_calls:1,total_duration_ms:4},answer:{direct_answer:{text:malicious,evidence_ids:['E1']},key_points:[{text:malicious,evidence_ids:['E1']}],limitations:[malicious]},citations:[{evidence_id:'E1',chunk_id:'chunk-1'}]})};}
 throw Error('unexpected fetch');
};
class FormData {get(key){return {symbol:'NVDA',question:'What risks?',form:''}[key];}}
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,window:{scrollTo(){},setTimeout(){}},URL,FormData,fetch,console});
const flatten=(item)=>[item,...item.children.flatMap(flatten)];
setTimeout(async()=>{
 assert.strictEqual(answerCalls,0);
 await submitHandler({preventDefault(){},currentTarget:form});
 assert.strictEqual(searchCalls,1);
 assert.ok(answerHandler);
 assert.match(results.innerHTML,/生成中文回答（本地模型）/);
 await answerHandler();
 assert.strictEqual(answerCalls,1);
 assert.ok(!answerContainer.innerHTML.includes(malicious));
 const all=flatten(answerContainer);
 assert.ok(all.some(item=>item.textContent===malicious));
 const citation=all.find(item=>item.className==='answer-citation');
 assert.ok(citation); citation.listeners.click();
 assert.strictEqual(more.open,true); assert.strictEqual(evidenceCard.scrolled,true);
 assert.strictEqual(evidenceCard.classList['citation-highlight'],true);
 failAnswer=true;
 await answerHandler();
 assert.strictEqual(answerCalls,2);
 assert.match(results.innerHTML,/Synthetic complete sentence/);
 assert.ok(flatten(answerContainer).some(item=>item.textContent.includes('本地模型暂不可用')));
 assert.strictEqual(nodes['#local-model-count'].textContent,'本次检索的 LLM 调用：0');
 process.stdout.write('opt-in answer checks passed\n');
},0);
"""
        result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "opt-in answer checks passed")


if __name__ == "__main__":
    unittest.main()
