import json,os,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
from finsight_rag.catalog import SecurityCatalog
from finsight_rag.coverage import rag_coverage
ROOT=Path(__file__).parent; SCRIPT=(ROOT.parent/'scripts/build_sec_corpus.py').resolve()
class CorpusTests(unittest.TestCase):
 def make_root(self):
  d=Path(tempfile.mkdtemp()); (d/'.local_data/sec/normalized').mkdir(parents=True); shutil.copy(ROOT/'fixtures/sec_ticker_mapping.synthetic.json',d/'.local_data/sec/normalized/mapping.json'); shutil.copy(ROOT/'fixtures/sec_submissions_nvda.synthetic.json',d/'.local_data/sec/normalized/0001045810_submissions.json'); return d
 def test_catalog_search_and_coverage(self):
  c=SecurityCatalog.from_json(ROOT/'fixtures/sec_ticker_mapping.synthetic.json'); self.assertEqual(c.resolve(' nvda ')['cik'],'0001045810'); self.assertEqual(c.search('Syn',2)[0]['ticker'],'AMD'); self.assertEqual(rag_coverage(c.resolve('NVDA'),[] )['status'],'not_built'); self.assertEqual(rag_coverage(c.resolve('NVDA'),[{'ticker':'NVDA','cik':'0001045810','status':'available','filing_count':2,'chunk_count':3}])['chunk_count'],3)
 def test_candidate_cli_isolated(self):
  d=self.make_root()
  try:
   out=d/'.local_data/candidates.json'; env={**os.environ,'PYTHONPATH':str(ROOT.parent/'src')}; r=subprocess.run([sys.executable,str(SCRIPT),'--ticker-mapping','.local_data/sec/normalized/mapping.json','--submissions-dir','.local_data/sec/normalized','--output','.local_data/candidates.json','--candidate-only','--as-of','2024-12-31T23:59:59Z','--symbols','NVDA,AMD'],cwd=d,env=env,capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr); data=json.loads(out.read_text()); self.assertFalse(data['network_executed']); self.assertEqual(data['candidates'][1]['status'],'missing_submissions'); self.assertEqual(data['candidates'][0]['stats']['selected_10k'],1)
  finally: shutil.rmtree(d)
 def test_network_missing_agent_stops_before_request(self):
  d=self.make_root()
  try:
   env={k:v for k,v in os.environ.items() if k!='FINSIGHT_SEC_USER_AGENT'}; env['PYTHONPATH']=str(ROOT.parent/'src'); r=subprocess.run([sys.executable,str(SCRIPT),'--candidate-manifest','.local_data/candidates.json','--output-dir','.local_data/rag/corpus','--network'],cwd=d,env=env,capture_output=True,text=True); self.assertNotEqual(r.returncode,0); self.assertIn('FINSIGHT_SEC_USER_AGENT',r.stderr)
  finally: shutil.rmtree(d)
 def test_catalog_limit_zero(self): self.assertEqual(SecurityCatalog.from_json(ROOT/'fixtures/sec_ticker_mapping.synthetic.json').search('',0),[])
 def test_catalog_prefix(self): self.assertGreaterEqual(len(SecurityCatalog.from_json(ROOT/'fixtures/sec_ticker_mapping.synthetic.json').search('N')),1)
 def test_catalog_unknown(self):
  with self.assertRaises(KeyError): SecurityCatalog.from_json(ROOT/'fixtures/sec_ticker_mapping.synthetic.json').resolve('ZZZ')
 def test_coverage_partial(self): self.assertEqual(rag_coverage({'ticker':'NVDA','cik':'0001045810'},[{'ticker':'NVDA','cik':'0001045810','status':'partial'}])['status'],'partial')
 def test_coverage_isolated(self): self.assertEqual(rag_coverage({'ticker':'AMD','cik':'0000002488'},[{'ticker':'NVDA','cik':'0001045810','status':'available'}])['status'],'not_built')
if __name__=='__main__': unittest.main()
