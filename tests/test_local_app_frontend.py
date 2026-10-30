"""Synthetic browser-shell contract checks without SEC data or a network."""

from pathlib import Path
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "prototype" / "app.js"
INDEX_HTML = APP_JS.with_name("index.html")


class LocalAppFrontendTests(unittest.TestCase):
    def test_html_versions_updated_static_assets(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('app.js?v=research-records-20261030', html)
        self.assertIn('styles.css?v=research-records-20261030', html)

    def test_research_records_are_read_only_escaped_and_record_scoped(self):
        """Synthetic contract check: history uses only record GETs and local citation targets."""
        source = APP_JS.read_text(encoding="utf-8")
        self.assertIn("fetch(`/api/research-records?${query.toString()}`)", source)
        self.assertIn("fetch(`/api/research-records/${encodeURIComponent(recordId)}`)", source)
        self.assertNotIn("/api/sec/evidence-search", source[source.index("async function researchRecords"):source.index("function openModal")])
        self.assertNotIn("/api/sec/answer", source[source.index("async function researchRecords"):source.index("function openModal")])
        self.assertIn("escapeHtml(record.question", source)
        self.assertIn("data-evidence-target", source)
        self.assertIn("data-evidence-id", source)
        self.assertIn("事实内容尚未人工核验", source)
        self.assertIn("研究记录暂时不可用", source)
        self.assertIn("回答已生成，但研究记录", source)
        self.assertIn("pending_human_review: '待人工复核'", source)
        self.assertIn("statusLabel(record.review_status || 'unreviewed')", source)

    def test_research_record_compare_view_uses_saved_windows_and_isolated_selection(self):
        source = APP_JS.read_text(encoding="utf-8")
        self.assertIn("record-comparison-grid", source)
        self.assertIn("record-compare-button", source)
        self.assertIn("recordWindowCard(item, item.evidence_id, true)", source)
        self.assertIn("packedEvidence", source)
        self.assertIn("本段引用", source)
        self.assertIn("其他入模证据", source)
        self.assertIn("引用关联不等于事实支持，请核对原文", source)
        self.assertIn("当前为只读对照，尚未完成人工核验", source)
        self.assertIn("let recordDetailRequest = 0", source)
        self.assertIn("if (requestId !== recordDetailRequest) return", source)
        self.assertNotIn("/api/sec/evidence-search", source[source.index("async function researchRecordDetail"):source.index("function openModal")])
        self.assertNotIn("/api/sec/answer", source[source.index("async function researchRecordDetail"):source.index("function openModal")])

    def test_research_record_compare_runtime_switches_segments_and_keeps_zero_model_calls(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert'); let clickHandler,fetchCalls=[];
class Node { constructor(selector=''){this.selector=selector;this.children=[];this.dataset={};this.listeners={};this.classList={add(){},remove(){},toggle(){}};}
 set innerHTML(v){this._html=String(v);this.children=[];if(this.selector==='#app'&&this._html.includes('record-row')){['a','b'].forEach(id=>{let n=new Node('.record-row');n.dataset.recordId=id;this.children.push(n);});}if(this.selector==='#app'&&this._html.includes('record-compare-button')){let n=new Node('.record-compare-button');n.dataset.segmentIndex='point-0';this.children.push(n);}}
 get innerHTML(){return this._html||'';} set textContent(v){this._text=String(v);} get textContent(){return this._text||'';} addEventListener(t,f){this.listeners[t]=f;} querySelector(s){if(s==='#record-comparison')return nodes[s];return this.children.find(n=>n.selector===s)||nodes[s]||new Node(s);} querySelectorAll(s){return this.children.filter(n=>n.selector===s);} closest(){return null;} setAttribute(){} scrollIntoView(){this.scrolled=true;} }
const nodes={};['#app','#modal','#modal-body','#modal-title','#page-title','#page-eyebrow','#global-notice','#environment-label','#sidebar-state','.close','#record-comparison'].forEach(k=>nodes[k]=new Node(k));
const document={querySelector:s=>nodes[s]||new Node(s),querySelectorAll:s=>nodes['#app'].children.filter(n=>n.selector===s),addEventListener:(t,f)=>{if(t==='click'&&!clickHandler)clickHandler=f;},createElement:t=>new Node(t)};
const rec=(id,delay)=>new Promise(resolve=>setTimeout(()=>resolve({ok:true,json:async()=>({record_id:id,symbol:id==='a'?'NVDA':'AAPL',question:id,answer:{direct_answer:{text:id+' answer',evidence_ids:['E1']},key_points:[{text:id+' point',evidence_ids:id==='a'?['E1','E2']:[]}]},packed_evidence:[{evidence_id:'E1',symbol:id,company_name:'Synthetic',form:'10-Q',filing_date:'2026-01-01',accession_number:'same',evidence_excerpt:id+' window one',source_url:'https://www.sec.gov/Archives/a.htm'},{evidence_id:'E2',symbol:id,company_name:'Synthetic',form:'10-Q',filing_date:'2026-01-01',accession_number:'same',evidence_excerpt:id+' window two',source_url:'https://www.sec.gov/Archives/a.htm'}],evidence:[],citations:[{evidence_id:'E1',accession_number:'same',chunk_id:'c1',source_url:'https://www.sec.gov/Archives/a.htm'}],save_status:'saved',review_status:'pending_human_review'})}),delay));
const fetch=async url=>{fetchCalls.push(url);if(url==='/api/health')return {ok:true,json:async()=>({corpus_as_of:'synthetic',document_count:1,chunk_count:1})};if(url.startsWith('/api/research-records?'))return {ok:true,json:async()=>({items:[{record_id:'a',symbol:'NVDA',question:'a'},{record_id:'b',symbol:'AAPL',question:'b'}],total:2,limit:10,offset:0})};if(url.endsWith('/a'))return rec('a',30);if(url.endsWith('/b'))return rec('b',5);throw Error(url)};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,window:{scrollTo(){},setTimeout},URL,URLSearchParams,FormData,fetch,console});
 setTimeout(async()=>{clickHandler({target:{closest:()=>({dataset:{view:'history'}})}});await new Promise(r=>setTimeout(r,60));let rows=nodes['#app'].children.filter(n=>n.selector==='.record-row');assert.equal(rows.length,2);rows[0].listeners.click();rows[1].listeners.click();await new Promise(r=>setTimeout(r,180));assert(nodes['#app'].innerHTML.includes('AAPL · 研究记录'), nodes['#app'].innerHTML);assert(nodes['#app'].innerHTML.includes('b answer'));assert(!nodes['#app'].innerHTML.includes('a answer'));assert(nodes['#app'].innerHTML.includes('b window one'));assert(!nodes['#app'].innerHTML.includes('a window one'));let compareButton=nodes['#app'].children.find(n=>n.selector==='.record-compare-button');assert(compareButton&&typeof compareButton.listeners.click==='function');compareButton.listeners.click();assert(nodes['#record-comparison'].innerHTML.includes('b point'));assert.equal(fetchCalls.filter(x=>x.includes('/api/sec/')).length,0);process.stdout.write('compare race runtime passed\n')},0);
'''
        result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "compare race runtime passed")

    def test_research_record_runtime_switches_all_evidence_labels_with_selected_segment(self):
        """Synthetic VM regression: all-window labels follow the selected paragraph refs."""
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');let clickHandler,fetchCalls=[];
class Node{constructor(selector=''){this.selector=selector;this.children=[];this.dataset={};this.listeners={};this.classList={add(){},remove(){},toggle(){}};}
 set innerHTML(v){this._html=String(v);this.children=[];if(this.selector==='#app'&&this._html.includes('record-row')){const n=new Node('.record-row');n.dataset.recordId='a';this.children=[n];}
  if(this.selector==='#app'&&this._html.includes('record-compare-button')){for(const index of ['direct','point-0','point-1','point-2','point-3']){const n=new Node('.record-compare-button');n.dataset.segmentIndex=index;this.children.push(n);}}
  if(this.selector==='#app'&&this._html.includes('record-all-evidence')){nodes['.record-all-evidence']._html=(this._html.match(/<details class="record-all-evidence">[\s\S]*?<\/details>/)||[''])[0];nodes['#record-comparison']._html=(this._html.match(/<div id="record-comparison">([\s\S]*?)<\/div>/)||['',''])[1];}
 }
 get innerHTML(){return this._html||'';}get textContent(){return this._text||'';}set textContent(v){this._text=String(v);}
 addEventListener(t,f){this.listeners[t]=f;}querySelector(s){if(s==='#record-comparison')return nodes[s];if(s==='.record-all-evidence')return nodes[s];if(s==='.record-all-evidence .evidence-list')return nodes['.record-all-evidence'];return this.children.find(n=>n.selector===s)||nodes[s]||new Node(s);}
 querySelectorAll(s){return this.children.filter(n=>n.selector===s);}closest(){return null;}setAttribute(){}scrollIntoView(){}
}
const nodes={};for(const k of ['#app','#record-comparison','.record-all-evidence','.record-all-evidence .evidence-list','#modal','#modal-body','#modal-title','#page-title','#page-eyebrow','#global-notice','#environment-label','#sidebar-state','.close'])nodes[k]=new Node(k);
const document={querySelector:s=>s==='.record-all-evidence .evidence-list'?nodes['.record-all-evidence']:nodes[s]||new Node(s),querySelectorAll:s=>nodes['#app'].children.filter(n=>n.selector===s),addEventListener:(t,f)=>{if(t==='click'&&!clickHandler)clickHandler=f;},createElement:t=>new Node(t)};
const record={record_id:'a',symbol:'NVDA',question:'synthetic',answer:{direct_answer:{text:'direct',evidence_ids:['E1']},key_points:[{text:'point E2',evidence_ids:['E2']},{text:'point E2 E3',evidence_ids:['E2','E3']},{text:'empty',evidence_ids:[]},{text:'missing E9',evidence_ids:['E9']}]},packed_evidence:[...['E1','E2','E3'].map((id,i)=>({evidence_id:id,symbol:'NVDA',company_name:'Synthetic',form:'10-Q',filing_date:'2026-01-01',accession_number:'same',evidence_excerpt:id+' window'}))],evidence:[],citations:[],save_status:'saved',review_status:'pending_human_review'};
const fetch=async url=>{fetchCalls.push(url);if(url==='/api/health')return {ok:true,json:async()=>({})};if(url.startsWith('/api/research-records?'))return {ok:true,json:async()=>({items:[{record_id:'a',symbol:'NVDA',question:'synthetic'}],total:1,limit:10,offset:0})};if(url.endsWith('/a'))return {ok:true,json:async()=>record};throw Error(url)};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,window:{scrollTo(){},setTimeout},URL,URLSearchParams,FormData,fetch,console});
setTimeout(async()=>{clickHandler({target:{closest:()=>({dataset:{view:'history'}})}});await new Promise(r=>setTimeout(r,30));nodes['#app'].children.find(n=>n.selector==='.record-row').listeners.click();await new Promise(r=>setTimeout(r,30));
 const buttons=nodes['#app'].children.filter(n=>n.selector==='.record-compare-button');assert.equal(buttons.length,5);
 const all=nodes['.record-all-evidence'];assert.match(all.innerHTML,/record-window-referenced" data-evidence-id="E1"/);assert.match(all.innerHTML,/其他入模证据 · Accession：same/);
 buttons[1].listeners.click();assert.match(nodes['#record-comparison'].innerHTML,/point E2/);assert.match(all.innerHTML,/record-window-referenced" data-evidence-id="E2"/);assert.doesNotMatch(all.innerHTML,/record-window-referenced" data-evidence-id="E1"/);assert.match(nodes['#record-comparison'].innerHTML,/本段引用：1 个窗口/);
 buttons[2].listeners.click();assert.match(nodes['#record-comparison'].innerHTML,/point E2 E3/);assert.match(all.innerHTML,/record-window-referenced" data-evidence-id="E2"/);assert.match(all.innerHTML,/record-window-referenced" data-evidence-id="E3"/);assert.match(nodes['#record-comparison'].innerHTML,/本段引用：2 个窗口/);
 buttons[3].listeners.click();assert.doesNotMatch(all.innerHTML,/record-window-referenced/);assert.match(nodes['#record-comparison'].innerHTML,/本段没有可用引用窗口/);
 buttons[4].listeners.click();assert.doesNotMatch(all.innerHTML,/record-window-referenced/);assert.match(nodes['#record-comparison'].innerHTML,/缺失引用目标：E9/);
 buttons[0].listeners.click();assert.match(all.innerHTML,/record-window-referenced" data-evidence-id="E1"/);assert.doesNotMatch(all.innerHTML,/record-window-referenced" data-evidence-id="E2"/);assert.equal(fetchCalls.filter(x=>x.includes('/api/sec/')).length,0);process.stdout.write('segment evidence labels runtime passed\n')},0);
'''
        result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "segment evidence labels runtime passed")

    def test_research_record_runtime_xss_and_no_model_calls(self):
        script = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const malicious = '<img src=x onerror=alert(1)><script>alert(2)</script>';
let documentClick, fetchCalls = [], recordRow;
class Node {
  constructor(selector='') { this.selector=selector; this.children=[]; this.dataset={}; this.listeners={}; this.classList={add(){},remove(){}}; this.open=false; }
  set innerHTML(value) { this._html=String(value); this.children=[]; if (this.selector==='#app' && this._html.includes('record-row')) { recordRow=new Node('.record-row'); recordRow.dataset.recordId='r-1'; this.children=[recordRow]; } if (this.selector==='#app' && this._html.includes('record-citation')) { const cite=new Node('.record-citation'); cite.dataset.evidenceTarget='E1'; this.children=[cite]; } }
  get innerHTML(){return this._html||'';}
  get textContent(){return this._text||'';} set textContent(v){this._text=String(v);}
  addEventListener(type, fn){this.listeners[type]=fn; if(this.selector==='.record-row' && type==='click') globalThis.lastRecordClick=fn;}
  querySelector(sel){ return this.children.find(n=>n.selector===sel) || nodes[sel] || new Node(sel); }
  querySelectorAll(sel){ return this.children.filter(n=>n.selector===sel); }
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=items;}
  closest(sel){return sel==='[data-view]' ? this : null;}
  scrollIntoView(){}
  setAttribute(){}
  focus(){}
}
const nodes={}; ['#app','#modal','#modal-body','#modal-title','#page-title','#page-eyebrow','#global-notice','#environment-label','#sidebar-state','.close'].forEach(k=>nodes[k]=new Node(k));
const document={querySelector:k=>nodes[k]||new Node(k), querySelectorAll:k=>k==='.record-row'?nodes['#app'].children.filter(n=>n.selector==='.record-row'):k==='.record-citation'?nodes['#app'].children.filter(n=>n.selector==='.record-citation'):[], addEventListener:(type,fn)=>{if(type==='click'&&!documentClick)documentClick=fn;}, createElement:tag=>new Node(tag)};
const fetch=async(url,opts)=>{fetchCalls.push(url); if(url==='/api/health') return {ok:true,json:async()=>({corpus_as_of:'synthetic',document_count:1,chunk_count:1})}; if(url==='/api/securities') return {ok:true,json:async()=>({securities:[{symbol:'NVDA',company_name:'Synthetic',document_count:1,chunk_count:1,available_forms:[]}]})}; if(url.startsWith('/api/research-records?')) return {ok:true,json:async()=>({items:[{record_id:'r-1',symbol:'NVDA',question:malicious,created_at:'synthetic',save_status:'saved',review_status:'pending_human_review'}],total:1,limit:10,offset:0})}; if(url==='/api/research-records/r-1') return {ok:true,json:async()=>({record_id:'r-1',symbol:'NVDA',question:malicious,answer:{direct_answer:{text:malicious,evidence_ids:['E1']},key_points:[{text:malicious,evidence_ids:['E1','E9']}]},citations:[{evidence_id:'E1',accession_number:'a1',chunk_id:'c1',source_url:'https://www.sec.gov/Archives/a.htm'}],packed_evidence:[{evidence_id:'E1',symbol:'NVDA',company_name:'Synthetic',form:'10-Q',filing_date:'2026-01-01',accession_number:'a1',evidence_excerpt:malicious},{evidence_id:'E2',symbol:'NVDA',company_name:'Synthetic',form:'10-Q',filing_date:'2026-01-01',accession_number:'a1',evidence_excerpt:'safe second window'}],evidence:[{evidence_id:'E1',symbol:'NVDA',evidence_excerpt:malicious,source_url:'https://evil.example/?x=" onmouseover="alert(9)'}],save_status:'saved',review_status:'pending_human_review',data_as_of:'synthetic'})}; throw Error('unexpected network '+url);};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,window:{scrollTo(){},setTimeout},URL,URLSearchParams,FormData,fetch,console});
setTimeout(async()=>{ documentClick({target:{closest:()=>({dataset:{view:'history'}})}}); await new Promise(r=>setTimeout(r,50)); assert.ok(recordRow && typeof recordRow.listeners.click==='function'); recordRow.listeners.click(); await new Promise(r=>setTimeout(r,50)); const html=nodes['#app'].innerHTML; assert.ok(html.includes('回答—证据对照')); assert.ok(html.includes('本段引用')); assert.ok(html.includes('其他入模证据')); assert.ok(html.includes('引用目标缺失：E9')); assert.ok(html.includes('未提供')); assert.ok(!html.includes(malicious)); assert.ok(html.includes('&lt;img')); assert.ok(html.includes('&lt;script')); assert.ok(!html.includes('href="https://evil.example')); assert.ok(!html.includes('onmouseover=')); assert.ok(html.includes('待人工复核')); assert.ok(!html.includes('pending_human_review')); assert.deepStrictEqual(fetchCalls.filter(u=>u.includes('/api/sec/')),[]); process.stdout.write('research record runtime checks passed\n'); },0);
"""
        result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "research record runtime checks passed")

    def test_research_record_runtime_stale_failure_cannot_replace_new_detail(self):
        """A late failed detail request must not overwrite the newer record."""
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');let clickHandler;
class Node{constructor(selector=''){this.selector=selector;this.children=[];this.dataset={};this.listeners={};this.classList={add(){},remove(){},toggle(){}};}set innerHTML(v){this._html=String(v);this.children=[];if(this.selector==='#app'&&this._html.includes('record-row')){for(const id of ['a','b']){const n=new Node('.record-row');n.dataset.recordId=id;this.children.push(n);}}}get innerHTML(){return this._html||'';}set textContent(v){this._text=String(v);}get textContent(){return this._text||'';}addEventListener(t,f){this.listeners[t]=f;}querySelector(s){return nodes[s]||new Node(s);}querySelectorAll(s){return this.children.filter(n=>n.selector===s);}closest(){return null;}setAttribute(){}focus(){}scrollIntoView(){}}
const nodes={};for(const k of ['#app','#modal','#modal-body','#modal-title','#page-title','#page-eyebrow','#global-notice','#environment-label','#sidebar-state','.close'])nodes[k]=new Node(k);
const document={querySelector:s=>nodes[s]||new Node(s),querySelectorAll:s=>nodes['#app'].children.filter(n=>n.selector===s),addEventListener:(t,f)=>{if(t==='click'&&!clickHandler)clickHandler=f;},createElement:t=>new Node(t)};
const detail=(id,delay,fail)=>new Promise((resolve,reject)=>setTimeout(()=>fail?reject(Error('stale failure')):resolve({ok:true,json:async()=>({record_id:id,symbol:id==='a'?'NVDA':'AAPL',question:id,answer:{direct_answer:{text:id+' answer',evidence_ids:[]},key_points:[]},packed_evidence:[],evidence:[],citations:[],save_status:'saved',review_status:'pending_human_review'})}),delay));
const fetch=async url=>{if(url==='/api/health')return {ok:true,json:async()=>({})};if(url.startsWith('/api/research-records?'))return {ok:true,json:async()=>({items:[{record_id:'a',symbol:'NVDA',question:'a'},{record_id:'b',symbol:'AAPL',question:'b'}],total:2,limit:10,offset:0})};if(url.endsWith('/a'))return detail('a',40,true);if(url.endsWith('/b'))return detail('b',5,false);throw Error(url)};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,window:{scrollTo(){},setTimeout},URL,URLSearchParams,FormData,fetch,console});setTimeout(async()=>{clickHandler({target:{closest:()=>({dataset:{view:'history'}})}});await new Promise(r=>setTimeout(r,30));const rows=nodes['#app'].children;rows[0].listeners.click();rows[1].listeners.click();await new Promise(r=>setTimeout(r,90));assert(nodes['#app'].innerHTML.includes('AAPL · 研究记录'));assert(!nodes['#app'].innerHTML.includes('研究记录损坏或不存在'));process.stdout.write('stale failure runtime passed\n')},0);
'''
        result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "stale failure runtime passed")

    def test_research_record_runtime_return_invalidates_late_detail_and_missing_fields_are_safe(self):
        """Leaving history invalidates a late success and incomplete evidence remains readable."""
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');let clickHandler;
class Node{constructor(selector=''){this.selector=selector;this.children=[];this.dataset={};this.listeners={};this.classList={add(){},remove(){},toggle(){}};}set innerHTML(v){this._html=String(v);this.children=[];if(this.selector==='#app'&&this._html.includes('record-row')){const n=new Node('.record-row');n.dataset.recordId='a';this.children=[n];}}get innerHTML(){return this._html||'';}set textContent(v){this._text=String(v);}get textContent(){return this._text||'';}addEventListener(t,f){this.listeners[t]=f;}querySelector(s){return nodes[s]||new Node(s);}querySelectorAll(s){return this.children.filter(n=>n.selector===s);}closest(){return null;}setAttribute(){}focus(){}scrollIntoView(){}}
const nodes={};for(const k of ['#app','#modal','#modal-body','#modal-title','#page-title','#page-eyebrow','#global-notice','#environment-label','#sidebar-state','.close'])nodes[k]=new Node(k);
const document={querySelector:s=>nodes[s]||new Node(s),querySelectorAll:s=>nodes['#app'].children.filter(n=>n.selector===s),addEventListener:(t,f)=>{if(t==='click'&&!clickHandler)clickHandler=f;},createElement:t=>new Node(t)};
const fetch=async url=>{if(url==='/api/health')return {ok:true,json:async()=>({})};if(url.startsWith('/api/research-records?'))return {ok:true,json:async()=>({items:[{record_id:'a',symbol:'NVDA',question:'a'}],total:1,limit:10,offset:0})};if(url.endsWith('/a'))return new Promise(resolve=>setTimeout(()=>resolve({ok:true,json:async()=>({record_id:'a',symbol:'NVDA',question:'a',answer:{direct_answer:{text:'a answer',evidence_ids:['E9']},key_points:[]},packed_evidence:[],evidence:[],citations:[],save_status:'saved',review_status:'pending_human_review'})}),50));throw Error(url)};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,window:{scrollTo(){},setTimeout},URL,URLSearchParams,FormData,fetch,console});setTimeout(async()=>{clickHandler({target:{closest:()=>({dataset:{view:'history'}})}});await new Promise(r=>setTimeout(r,20));const row=nodes['#app'].children[0];row.listeners.click();clickHandler({target:{closest:()=>({dataset:{view:'home'}})}});await new Promise(r=>setTimeout(r,90));assert(!nodes['#app'].innerHTML.includes('a answer'));assert(nodes['#app'].innerHTML.includes('搜索'));process.stdout.write('return invalidation runtime passed\n')},0);
'''
        result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "return invalidation runtime passed")

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
