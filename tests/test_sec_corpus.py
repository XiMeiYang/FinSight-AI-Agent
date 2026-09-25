import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from finsight_rag.catalog import SecurityCatalog
from finsight_rag.coverage import rag_coverage
ROOT=Path(__file__).parent
class CorpusTests(unittest.TestCase):
 def test_catalog_search_and_coverage(self):
  c=SecurityCatalog.from_json('.local_data/sec/normalized/0000000000_ticker_mapping_20260921T114607Z.json')
  self.assertEqual(c.resolve(' nvda ')['cik'],'0001045810'); self.assertEqual(c.search('NVIDA',0),[])
  self.assertEqual(rag_coverage(c.resolve('NVDA'),[] )['status'],'not_built')
  self.assertEqual(rag_coverage(c.resolve('NVDA'),[{'ticker':'NVDA','cik':'0001045810','status':'available','filing_count':2,'chunk_count':3}])['chunk_count'],3)
 def test_candidate_cli(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'c.json'; r=subprocess.run([sys.executable,'scripts/build_sec_corpus.py','--ticker-mapping','.local_data/sec/normalized/0000000000_ticker_mapping_20260921T114607Z.json','--submissions-dir','.local_data/sec/normalized','--output',str(out),'--candidate-only'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0); data=json.loads(out.read_text()); self.assertFalse(data['network_executed']); self.assertLessEqual(data['per_company_stats'][0]['stats']['selected_10k'],5)
 def test_network_missing_agent_stops(self):
  r=subprocess.run([sys.executable,'scripts/build_sec_corpus.py','--ticker-mapping','x','--submissions-dir','x','--output','/tmp/x','--network'],capture_output=True,text=True,env={k:v for k,v in __import__('os').environ.items() if k!='FINSIGHT_SEC_USER_AGENT'})
  self.assertNotEqual(r.returncode,0); self.assertIn('FINSIGHT_SEC_USER_AGENT',r.stderr)
if __name__=='__main__': unittest.main()
