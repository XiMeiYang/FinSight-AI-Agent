import json,os,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
from finsight_rag.catalog import SecurityCatalog
from finsight_rag.coverage import rag_coverage
ROOT=Path(__file__).parent; SCRIPT=(ROOT.parent/'scripts/build_sec_corpus.py').resolve()
class CorpusTests(unittest.TestCase):
 def load_script(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('corpus_script',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
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
 def test_refresh_metadata_fake_writes_submission(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('corpus_script',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
  class Fake:
   request_metadata=[{'attempt_count':1,'retry_count':0}]
   def submissions(self,cik): return {'cik':int(cik),'filings':{'recent':{'form':[]}}}
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    root=Path('.local_data'); (root/'sec/normalized').mkdir(parents=True); shutil.copy(ROOT/'fixtures/sec_ticker_mapping.synthetic.json',root/'sec/normalized/map.json'); c=SecurityCatalog.from_json(root/'sec/normalized/map.json'); r=mod.refresh_metadata(c,root/'sec/normalized',['AMD'],Fake()); self.assertTrue(r['network_executed']); self.assertTrue(list((root/'sec/normalized').glob('*0000002488*json')))
   finally: os.chdir(old)
 def test_primary_download_symbol_conversion_and_ingestion(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('corpus_script',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
  class Fake:
   request_metadata=[{'attempt_count':1,'retry_count':0}]
   def download_raw(self,url): raw=b'<html><body>Item 1 Business Synthetic filing</body></html>'; return (raw, __import__('hashlib').sha256(raw).hexdigest())
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    root=Path('.local_data'); root.mkdir(); manifest={'as_of':'2024-12-31T23:59:59Z','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[{'ticker':'TEST','cik':'0000000001','form':'10-K','filing_date':'2024-01-01','report_date':'2023-12-31','accepted_at':'20240101170000','published_at':'2024-01-01','accession_number':'0000000001-24-000001','primary_document':'test.htm','source_url':'https://www.sec.gov/Archives/edgar/data/1/000000000124000001/test.htm'}]}]}
    result=mod.download_corpus(manifest,'.local_data/rag/corpus','test@example.invalid',Fake()); self.assertEqual(result['document_count'],1); files=list(root.glob('rag/corpus/TEST/filings/*/document.json')); self.assertEqual(len(files),1); doc=json.loads(files[0].read_text()); self.assertEqual(doc['symbol'],'TEST'); self.assertEqual(doc['cik'],'0000000001')
   finally: os.chdir(old)

 def test_plan_latest_and_budgets_is_offline(self):
  mod=self.load_script(); rows=[]
  for company_i,ticker in enumerate(('A','B','C','D','E'),1):
   rows.append({'ticker':ticker,'cik':'0000000001','selected':[{'ticker':ticker,'cik':'0000000001','form':f,'filing_date':'2024-02-01','accepted_at':'20240201170000','accession_number':f'0000000001-24-{company_i*10+i:06d}','primary_document':'a.htm','source_url':f'https://www.sec.gov/Archives/edgar/data/1/0000000001240000{company_i*10+i}/a.htm'} for i,f in enumerate(('10-K','10-Q'),1)]})
  m={'as_of':'2024-12-31','candidates':rows}; r=mod.download_corpus(m,'.local_data/rag/corpus','',dry_run=True,latest_per_form_per_company=True)
  self.assertEqual(r['planned_document_count'],10); self.assertFalse(r['network_executed']); self.assertEqual(r['request_count'],0)
  self.assertEqual(mod.download_corpus(m,'.local_data/rag/corpus','',dry_run=True,max_documents=3,max_documents_per_company=1)['planned_document_count'],3)

 def test_complete_existing_is_skipped_without_download(self):
  mod=self.load_script()
  class Fake:
   request_metadata=[]
   def download_raw(self, url): return (b'<html><body>Item 1 Synthetic filing</body></html>', __import__('hashlib').sha256(b'<html><body>Item 1 Synthetic filing</body></html>').hexdigest())
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    m={'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[{'ticker':'TEST','cik':'0000000001','form':'10-K','filing_date':'2024-01-01','accepted_at':'20240101170000','accession_number':'0000000001-24-000001','primary_document':'a.htm','source_url':'https://www.sec.gov/Archives/edgar/data/1/000000000124000001/a.htm'}]}]}
    first=mod.download_corpus(m,'.local_data/rag/corpus','ua@example.invalid',Fake())
    self.assertEqual(first['completed_document_count'],1)
    class NoNetwork(Fake):
     def download_raw(self, url): raise AssertionError('network should not be called')
    second=mod.download_corpus(m,'.local_data/rag/corpus','ua@example.invalid',NoNetwork())
    self.assertEqual(second['already_completed_count'],1); self.assertEqual(second['request_count'],0)
   finally: os.chdir(old)

 def test_incomplete_existing_fails_without_network(self):
  mod=self.load_script()
  class Fake:
   request_metadata=[]
   def download_raw(self, url): raise AssertionError('network should not be called')
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    p=Path('.local_data/rag/corpus/TEST/raw'); p.mkdir(parents=True); (p/'000000000124000001.bin').write_bytes(b'x')
    m={'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[{'ticker':'TEST','cik':'0000000001','form':'10-K','filing_date':'2024-01-01','accession_number':'0000000001-24-000001','primary_document':'a.htm','source_url':'https://www.sec.gov/Archives/edgar/data/1/000000000124000001/a.htm'}]}]}
    r=mod.download_corpus(m,'.local_data/rag/corpus','ua@example.invalid',Fake()); self.assertEqual(r['failed_document_count'],1)
   finally: os.chdir(old)

 def test_candidate_identity_and_url_rejected_before_network(self):
  mod=self.load_script(); base={'ticker':'TEST','cik':'0000000001','form':'10-K','filing_date':'2024-01-01','accession_number':'0000000001-24-000001','primary_document':'a.htm','source_url':'https://www.sec.gov/Archives/edgar/data/1/000000000124000001/a.htm'}
  for key,val in [('ticker','../TEST'),('accession_number','bad'),('primary_document','../a.htm'),('source_url','https://www.sec.gov/Archives/edgar/data/1/x/a.htm')]:
   row=dict(base); row[key]=val
   with self.assertRaises(ValueError): mod.validate_candidate({'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[row]}]})

 def test_negative_budget_rejected_and_dry_run_privacy(self):
  mod=self.load_script(); m={'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[]}]}
  with self.assertRaises(ValueError): mod.download_corpus(m,'.local_data/rag/corpus','',dry_run=True,max_documents=-1)
  out=mod.download_corpus(m,'.local_data/rag/corpus','',dry_run=True); self.assertNotIn('User-Agent',json.dumps(out)); self.assertEqual(out['request_count'],0)

 def test_digest_mismatch_is_failed_network_and_bytes_counted(self):
  mod=self.load_script()
  class Fake:
   request_metadata=[]
   def download_raw(self,url): return b'<html><body>synthetic</body></html>','0'*64
  m={'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[{'ticker':'TEST','cik':'0000000001','form':'10-K','filing_date':'2024-01-01','accession_number':'0000000001-24-000001','primary_document':'a.htm','source_url':'https://www.sec.gov/Archives/edgar/data/1/000000000124000001/a.htm'}]}]}
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    r=mod.download_corpus(m,'.local_data/rag/corpus','x@y.invalid',Fake()); self.assertTrue(r['network_executed']); self.assertGreater(r['downloaded_bytes'],0); self.assertEqual(r['completed_document_count'],0)
   finally: os.chdir(old)

 def _download_manifest(self, ticker='TEST', accession='0000000001-24-000001'):
  return {'as_of':'2024-12-31','candidates':[{'ticker':ticker,'cik':'0000000001','selected':[{'ticker':ticker,'cik':'0000000001','form':'10-K','filing_date':'2024-01-01','accepted_at':'20240101170000','accession_number':accession,'primary_document':'a.htm','source_url':'https://www.sec.gov/Archives/edgar/data/1/'+accession.replace('-','')+'/a.htm'}]}]}

 def test_symlink_company_or_subdir_rejected_before_download(self):
  mod=self.load_script(); m=self._download_manifest()
  class NoNetwork:
   request_metadata=[]
   def download_raw(self, url): raise AssertionError('network should not be called')
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    target=Path('.local_data/rag/corpus/TEST'); target.parent.mkdir(parents=True); target.symlink_to(Path('/tmp'))
    with self.assertRaises(ValueError): mod.download_corpus(m,'.local_data/rag/corpus','ua',NoNetwork())
   finally: os.chdir(old)

 def test_parser_failure_leaves_no_batch_directory(self):
  mod=self.load_script(); m=self._download_manifest()
  class Fake:
   request_metadata=[]
   def download_raw(self, url):
    raw=b'<html>synthetic</html>'; return raw, __import__('hashlib').sha256(raw).hexdigest()
  old_builder=mod.build_sec_ingestion
  mod.build_sec_ingestion=lambda *a,**k: (_ for _ in ()).throw(ValueError('parse'))
  try:
   with tempfile.TemporaryDirectory() as d:
    old=os.getcwd(); os.chdir(d)
    try:
     r=mod.download_corpus(m,'.local_data/rag/corpus','ua',Fake())
     self.assertEqual(r['status'],'failed'); self.assertFalse(list(Path('.local_data/rag/corpus/TEST').glob('.batch-*')))
     self.assertFalse([p for p in Path('.local_data/rag/corpus/TEST').rglob('*') if p.is_file()])
    finally: os.chdir(old)
  finally: mod.build_sec_ingestion=old_builder

 def test_overwrite_replace_failure_restores_old_outputs_and_other_filing(self):
  mod=self.load_script()
  m1=self._download_manifest('TEST','0000000001-24-000001')
  m2=self._download_manifest('TEST','0000000001-24-000002')
  m={'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':m1['candidates'][0]['selected']+m2['candidates'][0]['selected']}]}
  class Fake:
   request_metadata=[]
   def __init__(self): self.n=0
   def download_raw(self,url): self.n+=1; raw=(b'old' if self.n<3 else b'new'); return raw,__import__('hashlib').sha256(raw).hexdigest()
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    f=Fake(); self.assertEqual(mod.download_corpus(m,'.local_data/rag/corpus','ua',f)['completed_document_count'],2)
    before={p.relative_to(Path('.local_data/rag/corpus')).as_posix():p.read_bytes() for p in Path('.local_data/rag/corpus/TEST').rglob('*') if p.is_file()}
    orig=mod.os.replace; calls=[0]
    def fail_once(src,dst):
     calls[0]+=1
     if calls[0]==2: raise OSError('replace')
     return orig(src,dst)
    mod.os.replace=fail_once
    try: r=mod.download_corpus(m1,'.local_data/rag/corpus','ua',f,overwrite=True)
    finally: mod.os.replace=orig
    self.assertEqual(r['failed_document_count'],1)
    after={p.relative_to(Path('.local_data/rag/corpus')).as_posix():p.read_bytes() for p in Path('.local_data/rag/corpus/TEST').rglob('*') if p.is_file()}
    self.assertEqual(before,after); self.assertFalse(list(Path('.local_data/rag/corpus/TEST').rglob('.batch-*')))
   finally: os.chdir(old)

 def test_missing_artifact_and_hash_mismatch_fail_without_network(self):
  mod=self.load_script(); m=self._download_manifest()
  class Fake:
   request_metadata=[]
   def download_raw(self,url): raise AssertionError('network should not be called')
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    class Seed:
     request_metadata=[]
     def download_raw(self,url):
      raw=b'<html><body>Item 1 Synthetic filing</body></html>'; return raw,__import__('hashlib').sha256(raw).hexdigest()
    mod.download_corpus(m,'.local_data/rag/corpus','ua',Seed())
    raw=Path('.local_data/rag/corpus/TEST/filings/000000000124000001/raw.bin'); raw.write_bytes(b'changed')
    r=mod.download_corpus(m,'.local_data/rag/corpus','ua',Fake()); self.assertEqual(r['failed_document_count'],1); self.assertEqual(r['request_count'],0)
    raw.write_bytes(b'unchanged'); raw.unlink(); r=mod.download_corpus(m,'.local_data/rag/corpus','ua',Fake()); self.assertEqual(r['failed_document_count'],1); self.assertEqual(r['request_count'],0)
   finally: os.chdir(old)

 def test_bundle_backup_recovers_before_network(self):
  mod=self.load_script(); m=self._download_manifest()
  class Seed:
   request_metadata=[]
   def download_raw(self,url):
    raw=b'<html><body>Item 1 Synthetic filing</body></html>'; return raw,__import__('hashlib').sha256(raw).hexdigest()
  class NoNetwork(Seed):
   def download_raw(self,url): raise AssertionError('network should not be called')
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    mod.download_corpus(m,'.local_data/rag/corpus','ua',Seed())
    filings=Path('.local_data/rag/corpus/TEST/filings'); final=filings/'000000000124000001'; backup=filings/'.backup-000000000124000001'; os.replace(final,backup)
    r=mod.download_corpus(m,'.local_data/rag/corpus','ua',NoNetwork()); self.assertEqual(r['already_completed_count'],1); self.assertTrue(final.is_dir()); self.assertFalse(backup.exists())
   finally: os.chdir(old)

 def test_overwrite_success_replaces_bundle_and_counts(self):
  mod=self.load_script(); m=self._download_manifest()
  class Fake:
   request_metadata=[]
   def __init__(self): self.raw=b'<html><body>Item 1 old</body></html>'
   def download_raw(self,url): return self.raw,__import__('hashlib').sha256(self.raw).hexdigest()
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    f=Fake(); mod.download_corpus(m,'.local_data/rag/corpus','ua',f)
    p=Path('.local_data/rag/corpus/TEST/filings/000000000124000001/raw.bin'); before=p.read_bytes(); f.raw=b'<html><body>Item 1 new</body></html>'
    r=mod.download_corpus(m,'.local_data/rag/corpus','ua',f,overwrite=True)
    self.assertEqual(r['overwritten_document_count'],1); self.assertNotEqual(before,p.read_bytes()); self.assertTrue((p.parent/'metadata.json').exists())
   finally: os.chdir(old)

 def test_each_write_stage_failure_cleans_temp_and_final(self):
  mod=self.load_script(); m=self._download_manifest()
  class Fake:
   request_metadata=[]
   def download_raw(self,url):
    raw=b'<html><body>Item 1 synthetic failure probe</body></html>'; return raw,__import__('hashlib').sha256(raw).hexdigest()
  original=mod._write_json
  for fail_at in (1,2,3):
   calls=[0]
   def failing(path,obj):
    calls[0]+=1
    if calls[0]==fail_at: raise OSError('synthetic write failure')
    return original(path,obj)
   mod._write_json=failing
   with tempfile.TemporaryDirectory() as d:
    old=os.getcwd(); os.chdir(d)
    try:
     r=mod.download_corpus(m,'.local_data/rag/corpus','ua',Fake()); self.assertEqual(r['failed_document_count'],1)
     root=Path('.local_data/rag/corpus/TEST/filings'); self.assertFalse(list(root.glob('<accession>')))
     self.assertFalse([p for p in root.rglob('*') if p.is_file()]); self.assertFalse(list(root.glob('.batch-*')))
    finally: os.chdir(old)
  mod._write_json=original

 def test_privacy_fields_not_in_result_or_bundle(self):
  mod=self.load_script(); m=self._download_manifest()
  secret='Analyst private@example.invalid /Users/private/secret'
  class Fake:
   request_metadata=[]
   def download_raw(self,url): raise RuntimeError(secret)
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    r=mod.download_corpus(m,'.local_data/rag/corpus',secret,Fake()); rendered=json.dumps(r)
    self.assertNotIn(secret,rendered); self.assertNotIn('private@example.invalid',rendered); self.assertNotIn('/Users/',rendered)
    self.assertFalse([p for p in Path('.local_data/rag/corpus').rglob('*') if p.is_file()])
   finally: os.chdir(old)

 def test_partial_and_completed_statistics_are_exact(self):
  mod=self.load_script(); one=self._download_manifest()['candidates'][0]['selected'][0]; two=dict(one,accession_number='0000000001-24-000002',source_url=one['source_url'].replace('000001','000002'))
  two['source_url']='https://www.sec.gov/Archives/edgar/data/1/000000000124000002/a.htm'
  m={'as_of':'2024-12-31','candidates':[{'ticker':'TEST','cik':'0000000001','selected':[one,two]}]}
  class Fake:
   def __init__(self): self.request_metadata=[{'attempts_total':1,'retry_count':0},{'attempts_total':2,'retry_count':1}]; self.n=0
   def download_raw(self,url):
    self.n+=1
    if self.n==2: raise RuntimeError('second failed')
    raw=b'<html><body>Item 1 successful</body></html>'; return raw,__import__('hashlib').sha256(raw).hexdigest()
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd(); os.chdir(d)
   try:
    r=mod.download_corpus(m,'.local_data/rag/corpus','ua',Fake()); self.assertEqual({k:r[k] for k in ('planned_document_count','attempted_document_count','completed_document_count','already_completed_count','overwritten_document_count','failed_document_count','request_count','retry_count','model_calls','status')},{'planned_document_count':2,'attempted_document_count':2,'completed_document_count':1,'already_completed_count':0,'overwritten_document_count':0,'failed_document_count':1,'request_count':3,'retry_count':1,'model_calls':0,'status':'partial'})
   finally: os.chdir(old)

if __name__=='__main__': unittest.main()
