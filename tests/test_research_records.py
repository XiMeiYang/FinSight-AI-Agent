import json, tempfile, unittest
from pathlib import Path
from finsight_app.research_records import ResearchRecordStore, ResearchRecordNotFound, ResearchRecordCorrupt

class ResearchRecordsTests(unittest.TestCase):
 def setUp(self): self.t=tempfile.TemporaryDirectory(); self.p=Path(self.t.name)/'records.sqlite3'; self.s=ResearchRecordStore(self.p)
 def tearDown(self): self.s.close(); self.t.cleanup()
 def save(self,symbol='SYN',q='q',status='completed',n=2):
  return self.s.save(symbol=symbol,question=q,answer_status=status,answer={'status':status},citations=[{'evidence_id':'E1'}],evidence=[{'evidence_id':f'E{i}','chunk_id':f'c{i}','accession_number':f'a{i}','source_url':f'https://sec/{i}'} for i in range(1,n+1)],packed_evidence=[{'evidence_id':f'E{i}','chunk_id':f'c{i}','accession_number':f'a{i}','source_url':f'https://sec/{i}'} for i in range(1,n+1)],filters={'as_of':'2026'},generation={'model_digest':'d'},model_metadata={'prompt_hash':'p','corpus_fingerprint':'f'})
 def test_reopen_pagination_symbol_filter_and_isolation(self):
  a=self.save('AAA'); b=self.save('BBB'); self.s.close(); self.s=ResearchRecordStore(self.p)
  self.assertEqual(self.s.list('AAA')['total'],1); self.assertEqual(self.s.list(limit=1)['items'][0]['symbol'],'BBB'); self.assertEqual(self.s.get(a['record_id'])['symbol'],'AAA'); self.assertEqual(self.s.get(b['record_id'])['symbol'],'BBB')
 def test_full_unreferenced_window_and_metadata(self):
  x=self.s.get(self.save(n=3)['record_id']); self.assertEqual(len(x['evidence']),3); self.assertEqual(x['evidence'][2]['source_url'],'https://sec/3'); self.assertEqual(x['model_metadata']['prompt_hash'],'p'); self.assertEqual(x['generation']['model_digest'],'d')
 def test_unknown_and_corrupt_and_version_errors(self):
  with self.assertRaises(ResearchRecordNotFound): self.s.get('missing')
  rid=self.save()['record_id']; self.s._db.execute('UPDATE research_records SET payload_json=? WHERE record_id=?',(json.dumps({'schema_version':1}),rid)); self.s._db.commit()
  with self.assertRaises(ResearchRecordCorrupt): self.s.get(rid)
 def test_sql_injection_is_data(self):
  self.save("AAA' OR 1=1 --"); self.assertEqual(self.s.list("AAA' OR 1=1 --")['total'],1); self.assertEqual(self.s.list("' OR 1=1")['total'],0)
 def test_failure_status(self):
  x=self.s.save_failure(symbol='SYN',question='q',detail='failed'); r=self.s.get(x['record_id']); self.assertEqual(r['answer_status'],'failed'); self.assertEqual(r['review_status'],'not_reviewed')
 def test_rejects_ancestor_symlink(self):
  import os
  root=Path(self.t.name)/'real'; root.mkdir(); link=Path(self.t.name)/'link'; os.symlink(root,link)
  with self.assertRaises(Exception): ResearchRecordStore(link/'nested'/'x.sqlite3')

 def test_rejects_insecure_existing_custom_parent_without_chmod(self):
  import os, stat
  custom=Path(self.t.name)/'custom'; custom.mkdir(mode=0o755); os.chmod(custom,0o755)
  with self.assertRaises(Exception): ResearchRecordStore(custom/'x.sqlite3')
  self.assertEqual(stat.S_IMODE(os.stat(custom).st_mode),0o755)

 def test_store_permissions_0600_and_directory_0700(self):
     import os, stat
     self.assertEqual(stat.S_IMODE(os.stat(self.p.parent).st_mode), 0o700)
     self.assertEqual(stat.S_IMODE(os.stat(self.p).st_mode), 0o600)

 def test_save_failure_does_not_retry_model(self):
  from fastapi.testclient import TestClient
  from finsight_app.api import create_app
  attempts=[]
  class FailingStore(ResearchRecordStore):
   def save(self, **kwargs): attempts.append(kwargs); raise OSError('synthetic save failure')
  model=_Model(); response=TestClient(create_app(_Svc(),answer_service=model,research_record_store=FailingStore(self.p))).post('/api/sec/answer',json={'symbol':'SYN','question':'risk'})
  self.assertEqual(response.status_code,200); self.assertEqual(model.model_call_count,1); self.assertEqual(len(attempts),1); self.assertEqual(response.json()['research_record']['save_status'],'failed')

 def test_corrupt_record_api_returns_500(self):
     from fastapi.testclient import TestClient
     from finsight_app.api import create_app
     rid=self.save()['record_id']; self.s._db.execute('UPDATE research_records SET payload_json=? WHERE record_id=?', ('{"schema_version":1}',rid)); self.s._db.commit()
     response=TestClient(create_app(_Svc(), research_record_store=self.s)).get('/api/research-records/'+rid)
     self.assertEqual(response.status_code,500)

 def test_reopen_app_and_history_does_not_search_or_generate(self):
     from fastapi.testclient import TestClient
     from finsight_app.api import create_app
     rid=self.save()['record_id']; self.s.close(); reopened=ResearchRecordStore(self.p)
     class NoCall:
         def search(self, **kwargs): raise AssertionError('search called')
     response=TestClient(create_app(NoCall(), research_record_store=reopened)).get('/api/research-records/'+rid)
     self.assertEqual(response.status_code,200); self.assertEqual(response.json()['record_id'],rid)

try:
 from fastapi.testclient import TestClient
 from finsight_app.api import create_app
except ImportError: TestClient = None

class _Svc:
 bm25_rows=[{'symbol':'SYN'}]
 def load(self): return self
 def health(self): return {'corpus_as_of':'2026-09-18T23:59:59Z','supported_symbols':['SYN']}
 def search(self, **kw):
  rows=[]
  for i in range(1,4): rows.append({'rank':i,'symbol':'SYN','evidence_excerpt':f'packed {i}.','chunk_id':f'c{i}','accession_number':f'a{i}','source_url':f'https://sec/{i}'})
  return {'filters':{'as_of':kw['as_of']},'results':rows}
class _Model:
 model_call_count=0
 def generate(self, question, retrieval_payload, request_callback=None):
  self.model_call_count+=1
  packed=[{'evidence_id':f'E{i}','evidence_excerpt':f'packed {i}.','chunk_id':f'c{i}','accession_number':f'a{i}','source_url':f'https://sec/{i}'} for i in range(1,4)]
  if request_callback: request_callback({'packed_evidence':packed,'original_rows':packed,'prompt_hash':'ph'})
  return {'answer_status':'completed','answer':{'direct_answer':{'text':'答','evidence_ids':['E1']}},'citations':[{'evidence_id':'E1'}],'evidence':[packed[0]],'generation':{'model_digest':'md'}}

@unittest.skipIf(TestClient is None,'fastapi unavailable')
class ApiRecordIntegrationTests(unittest.TestCase):
 def test_post_then_history_keeps_all_packed_and_history_is_read_only(self):
  with tempfile.TemporaryDirectory() as d:
   store=ResearchRecordStore(Path(d)/'r.sqlite3'); model=_Model(); client=TestClient(create_app(_Svc(),answer_service=model,research_record_store=store))
   out=client.post('/api/sec/answer',json={'symbol':'SYN','question':'risk'}); self.assertEqual(out.status_code,200); rid=out.json()['research_record']['record_id']; detail=client.get('/api/research-records/'+rid).json(); self.assertEqual(len(detail['evidence']),3); self.assertEqual(detail['data_as_of'],'2026-09-18T23:59:59Z'); self.assertEqual(detail['evidence'][2]['chunk_id'],'c3'); self.assertIsNone(detail['model_metadata']['corpus_fingerprint']['bm25_manifest_sha256']); self.assertIsNone(detail['model_metadata']['corpus_fingerprint']['dense_manifest_sha256'])
   before=model.model_call_count; self.assertEqual(client.get('/api/research-records').status_code,200); self.assertEqual(model.model_call_count,before)

if __name__=='__main__': unittest.main()
