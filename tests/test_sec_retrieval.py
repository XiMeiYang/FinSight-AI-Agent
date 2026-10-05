import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest import mock
from finsight_rag.bm25 import BM25Index
from finsight_rag.evaluation import EVALUATION_SCHEMA,evaluate,load_queries,percentile
from finsight_rag.retrieval import build_index,load_corpus,load_index,search
from finsight_rag.tokenizer import TOKENIZER_VERSION,tokenize,validate_query

def sha(data): return hashlib.sha256(data).hexdigest()

class RetrievalTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.local=Path(self.temp.name)/'.local_data'; self.corpus=self.local/'rag/corpus'; self.corpus.mkdir(parents=True)
  self.bundle('AAA','10-K','0000000001-26-000001','2026-01-01','revenue margin liquidity risk')
  self.bundle('AAA','10-Q','0000000001-26-000002','2026-04-01','quarterly revenue cash flow')
  self.bundle('BBB','10-K','0000000002-25-000001','2025-01-01','revenue margin liquidity risk')
  (self.corpus/'semiconductor-candidates-synthetic.json').write_text(json.dumps({'candidates':[{'ticker':'AAA','cik':'0000000001','company_name':'Alpha Synthetic Corp'},{'ticker':'BBB','cik':'0000000002','company_name':'Beta Synthetic Corp'}]}))
  self.index=self.local/'rag/indexes/test'
 def tearDown(self): self.temp.cleanup()
 def bundle(self,symbol,form,accession,filing_date,text,*,chunk_id=None):
  directory=self.corpus/symbol/'filings'/accession.replace('-',''); directory.mkdir(parents=True)
  cik='0000000001' if symbol=='AAA' else '0000000002'; document_id=hashlib.sha256((symbol+accession).encode()).hexdigest()[:24]; chunk_id=chunk_id or hashlib.sha256((document_id+text).encode()).hexdigest()[:24]
  source=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/report.htm'; raw=f'<html>{text}</html>'.encode(); raw_hash=sha(raw)
  meta={'symbol':symbol,'ticker':symbol,'cik':cik,'form':form,'accession_number':accession,'document_id':document_id,'filing_date':filing_date,'accepted_at':filing_date+'T12:00:00Z','published_at':filing_date,'source_url':source,'raw_sha256':raw_hash}
  section={'section_id':'section-1','section_title':'Risk Factors','section_order':0,'start_offset':0,'end_offset':len(text),'text':text,'text_sha256':sha(text.encode())}
  document={**{k:meta[k] for k in ('symbol','cik','form','accession_number','document_id','filing_date','accepted_at','published_at','source_url')},'as_of':'2026-09-18T23:59:59Z','input_sha256':raw_hash,'sections':[section]}
  chunk={**{k:meta[k] for k in ('symbol','cik','form','accession_number','document_id','filing_date','accepted_at','source_url')},'chunk_id':chunk_id,'chunk_index':0,'section_id':'section-1','section_title':'Risk Factors','text':text,'text_sha256':sha(text.encode()),'citation':f'{symbol} | {form} | {accession} | Risk Factors | chunk 0 | {source}'}
  directory.joinpath('raw.bin').write_bytes(raw); directory.joinpath('metadata.json').write_text(json.dumps(meta)); directory.joinpath('document.json').write_text(json.dumps(document)); directory.joinpath('chunks.jsonl').write_text(json.dumps(chunk)+'\n')
  manifest={**{k:meta[k] for k in ('symbol','cik','form','accession_number','document_id')},'as_of':'2026-09-18T23:59:59Z','raw_sha256':raw_hash,'metadata_sha256':sha(directory.joinpath('metadata.json').read_bytes()),'document_sha256':sha(directory.joinpath('document.json').read_bytes()),'chunks_sha256':sha(directory.joinpath('chunks.jsonl').read_bytes()),'section_count':1,'chunk_count':1}
  directory.joinpath('ingestion-manifest.json').write_text(json.dumps(manifest)); return directory
 def refresh_manifest(self,bundle):
  manifest=json.loads((bundle/'ingestion-manifest.json').read_text())
  for name,key in [('metadata.json','metadata_sha256'),('document.json','document_sha256'),('chunks.jsonl','chunks_sha256')]: manifest[key]=sha((bundle/name).read_bytes())
  (bundle/'ingestion-manifest.json').write_text(json.dumps(manifest))

 def test_tokenizer_deterministic_financial_unicode_hyphen(self):
  text='AI–driven\u2003Revenue $1,200.50 15%'; self.assertEqual(tokenize(text),tokenize(text)); tokens=tokenize(text)
  self.assertIn('ai-driven',tokens); self.assertIn('ai',tokens); self.assertIn('driven',tokens); self.assertIn('1200.50',tokens); self.assertIn('15%',tokens); self.assertTrue(TOKENIZER_VERSION)
 def test_query_validation(self):
  with self.assertRaises(ValueError): validate_query('!!!')
  with self.assertRaises(ValueError): validate_query('a'*2001)
 def test_bm25_known_order_and_tie(self):
  index=BM25Index([['alpha'],['alpha','beta'],['beta']]); self.assertGreater(index.score(['alpha'],0),index.score(['alpha'],1)); self.assertEqual(index.score(['missing'],0),0)
 def test_build_manifest_search_prefilters_and_no_result(self):
  manifest=build_index(self.corpus,self.index); self.assertEqual(manifest['document_count'],3); self.assertEqual(manifest['chunk_count'],3); self.assertEqual(manifest['chunks_per_company'],{'AAA':2,'BBB':1}); self.assertFalse(manifest['network_executed']); self.assertEqual(manifest['model_calls'],0)
  result=search(self.index,'quarterly revenue',symbol='AAA',form='10-Q',as_of='2026-06-01',corpus=self.corpus); self.assertEqual(len(result),1); self.assertEqual(result[0]['form'],'10-Q'); self.assertEqual(result[0]['company_name'],'Alpha Synthetic Corp'); self.assertLessEqual(len(result[0]['evidence_preview']),400)
  self.assertEqual(search(self.index,'unmatchedterm',corpus=self.corpus),[])
  self.assertEqual(search(self.index,'quarterly',as_of='2026-02-01',corpus=self.corpus),[])
 def test_stable_tie_break(self):
  build_index(self.corpus,self.index); first=search(self.index,'revenue',corpus=self.corpus); second=search(self.index,'revenue',corpus=self.corpus); self.assertEqual([x['chunk_id'] for x in first],[x['chunk_id'] for x in second]); self.assertEqual(first[0]['symbol'],'AAA')
 def test_invalid_search_inputs(self):
  build_index(self.corpus,self.index)
  for kwargs in ({'top_k':0},{'top_k':51},{'symbol':'ZZZ'},{'form':'8-K'}):
   with self.assertRaises(ValueError): search(self.index,'revenue',corpus=self.corpus,**kwargs)
 def test_complete_skip_default_conflict_and_overwrite(self):
  first=build_index(self.corpus,self.index); second=build_index(self.corpus,self.index); self.assertEqual(second['status'],'already_completed'); self.assertEqual(first['index_id'],second['index_id'])
  with self.assertRaises(FileExistsError): build_index(self.corpus,self.index,k1=1.2)
  replaced=build_index(self.corpus,self.index,k1=1.2,overwrite=True); self.assertEqual(replaced['bm25']['k1'],1.2); load_index(self.index,self.corpus)
 def test_incomplete_index_and_corrupt_hash_fail(self):
  self.index.mkdir(parents=True); (self.index/'manifest.json').write_text('{}')
  with self.assertRaises(FileExistsError): build_index(self.corpus,self.index)
  import shutil; shutil.rmtree(self.index); build_index(self.corpus,self.index); (self.index/'documents.jsonl').write_text('changed')
  with self.assertRaises(ValueError): load_index(self.index,self.corpus)
 def test_schema_and_stale_corpus_fail(self):
  build_index(self.corpus,self.index); manifest=json.loads((self.index/'manifest.json').read_text()); manifest['schema_version']='future'; manifest['index_sha256']=sha(json.dumps({k:v for k,v in manifest.items() if k!='index_sha256'},sort_keys=True,separators=(',',':')).encode()); (self.index/'manifest.json').write_text(json.dumps(manifest))
  with self.assertRaises(ValueError): load_index(self.index,self.corpus)
  import shutil; shutil.rmtree(self.index); build_index(self.corpus,self.index); bundle=next(self.corpus.glob('AAA/filings/*')); (bundle/'raw.bin').write_bytes(b'changed')
  with self.assertRaises(ValueError): load_index(self.index,self.corpus)
 def test_bundle_hash_identity_citation_and_duplicate_fail(self):
  target=next(self.corpus.glob('AAA/filings/*'))
  (target/'raw.bin').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'hash'): load_corpus(self.corpus)
  self.tearDown(); self.setUp(); target=next(self.corpus.glob('AAA/filings/*')); rows=[json.loads((target/'chunks.jsonl').read_text())]; rows[0]['symbol']='BBB'; (target/'chunks.jsonl').write_text(json.dumps(rows[0])+'\n'); self.refresh_manifest(target)
  with self.assertRaisesRegex(ValueError,'identity'): load_corpus(self.corpus)
  self.tearDown(); self.setUp(); target=next(self.corpus.glob('AAA/filings/*')); row=json.loads((target/'chunks.jsonl').read_text()); row['citation']='bad'; (target/'chunks.jsonl').write_text(json.dumps(row)+'\n'); self.refresh_manifest(target)
  with self.assertRaisesRegex(ValueError,'citation'): load_corpus(self.corpus)
  self.tearDown(); self.setUp(); target=next(self.corpus.glob('AAA/filings/*')); row=json.loads((target/'chunks.jsonl').read_text()); row['citation']=row['citation'].replace('chunk 0','chunk 9'); (target/'chunks.jsonl').write_text(json.dumps(row)+'\n'); self.refresh_manifest(target)
  with self.assertRaisesRegex(ValueError,'citation'): load_corpus(self.corpus)
  self.tearDown(); self.setUp(); target=next(self.corpus.glob('AAA/filings/*')); row=json.loads((target/'chunks.jsonl').read_text()); row['chunk_index']=1; row['citation']=row['citation'].replace('chunk 0','chunk 10'); (target/'chunks.jsonl').write_text(json.dumps(row)+'\n'); self.refresh_manifest(target)
  with self.assertRaisesRegex(ValueError,'citation'): load_corpus(self.corpus)
  self.tearDown(); self.setUp(); target=next(self.corpus.glob('AAA/filings/*')); line=(target/'chunks.jsonl').read_text(); (target/'chunks.jsonl').write_text(line+line); manifest=json.loads((target/'ingestion-manifest.json').read_text()); manifest['chunk_count']=2; self.refresh_manifest(target)
  with self.assertRaisesRegex(ValueError,'duplicate'): load_corpus(self.corpus)
 def test_global_duplicate_chunk_fail(self):
  bundles=sorted(self.corpus.glob('*/filings/*')); first=json.loads((bundles[0]/'chunks.jsonl').read_text()); second=json.loads((bundles[1]/'chunks.jsonl').read_text()); second['chunk_id']=first['chunk_id']; (bundles[1]/'chunks.jsonl').write_text(json.dumps(second)+'\n'); self.refresh_manifest(bundles[1])
  with self.assertRaisesRegex(ValueError,'across'): load_corpus(self.corpus)
 def test_symlink_and_path_escape_rejected(self):
  with self.assertRaises(ValueError): build_index(self.corpus,Path(self.temp.name)/'outside')
  with self.assertRaises(ValueError): build_index(self.corpus,self.local/'../escaped')
  with self.assertRaises(ValueError): build_index(self.corpus,self.local/'rag/../../escaped')
  link=self.local/'rag/indexes/link'; link.parent.mkdir(parents=True); link.symlink_to(self.corpus,target_is_directory=True)
  with self.assertRaises(ValueError): build_index(self.corpus,link)
 def test_tampered_documents_or_postings_rejected_even_with_rehashed_manifest(self):
  build_index(self.corpus,self.index); documents=self.index/'documents.jsonl'; rows=documents.read_text().splitlines(); row=json.loads(rows[0]); row['text']='tampered'; rows[0]=json.dumps(row,sort_keys=True,separators=(',',':')); documents.write_text('\n'.join(rows)+'\n'); manifest=json.loads((self.index/'manifest.json').read_text()); manifest['documents_sha256']=sha(documents.read_bytes()); manifest['index_sha256']=sha(json.dumps({k:v for k,v in manifest.items() if k!='index_sha256'},sort_keys=True,separators=(',',':')).encode()); (self.index/'manifest.json').write_text(json.dumps(manifest))
  with self.assertRaisesRegex(ValueError,'provenance'): load_index(self.index,self.corpus)
  import shutil; shutil.rmtree(self.index); build_index(self.corpus,self.index); postings=self.index/'postings.json'; data=json.loads(postings.read_text()); data[next(iter(data))]={'0':999}; postings.write_text(json.dumps(data,sort_keys=True,separators=(',',':'))); manifest=json.loads((self.index/'manifest.json').read_text()); manifest['postings_sha256']=sha(postings.read_bytes()); manifest['index_sha256']=sha(json.dumps({k:v for k,v in manifest.items() if k!='index_sha256'},sort_keys=True,separators=(',',':')).encode()); (self.index/'manifest.json').write_text(json.dumps(manifest))
  with self.assertRaisesRegex(ValueError,'postings'): load_index(self.index,self.corpus)
 def test_derived_company_name_tamper_and_catalog_change_are_rejected(self):
  build_index(self.corpus,self.index); documents=self.index/'documents.jsonl'; rows=documents.read_text().splitlines(); row=json.loads(rows[0]); row['company_name']='Forged Corp'; rows[0]=json.dumps(row,sort_keys=True,separators=(',',':')); documents.write_text('\n'.join(rows)+'\n'); manifest=json.loads((self.index/'manifest.json').read_text()); manifest['documents_sha256']=sha(documents.read_bytes()); manifest['indexed_documents_sha256']=sha(json.dumps([{k:json.loads(line).get(k) for k in __import__('finsight_rag.retrieval',fromlist=['_INDEX_KEYS'])._INDEX_KEYS+('company_name','corpus_as_of')} for line in rows],sort_keys=True,separators=(',',':')).encode()); manifest['index_sha256']=sha(json.dumps({k:v for k,v in manifest.items() if k!='index_sha256'},sort_keys=True,separators=(',',':')).encode()); (self.index/'manifest.json').write_text(json.dumps(manifest))
  with self.assertRaisesRegex(ValueError,'derived'): load_index(self.index,self.corpus)
  import shutil; shutil.rmtree(self.index); build_index(self.corpus,self.index); catalog=self.corpus/'semiconductor-candidates-synthetic.json'; data=json.loads(catalog.read_text()); data['candidates'][0]['company_name']='Changed Corp'; catalog.write_text(json.dumps(data))
  with self.assertRaises(FileExistsError): build_index(self.corpus,self.index)
 def test_write_failure_cleans_temp(self):
  original=Path.write_text; calls=[0]
  def fail(path,*args,**kwargs):
   calls[0]+=1
   if calls[0]==2: raise OSError('synthetic write failure')
   return original(path,*args,**kwargs)
  with mock.patch.object(Path,'write_text',fail):
   with self.assertRaises(OSError): build_index(self.corpus,self.index)
  self.assertFalse(self.index.exists()); self.assertFalse(list(self.index.parent.glob('.test.batch-*')))
 def test_overwrite_commit_failure_restores_old_index(self):
  build_index(self.corpus,self.index); before={p.name:p.read_bytes() for p in self.index.iterdir()}; original=os.replace; calls=[0]
  def fail_second(source,destination):
   calls[0]+=1
   if calls[0]==2: raise OSError('synthetic commit failure')
   return original(source,destination)
  with mock.patch('finsight_rag.retrieval.os.replace',side_effect=fail_second):
   with self.assertRaises(OSError): build_index(self.corpus,self.index,overwrite=True,k1=1.2)
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.index.iterdir()}); load_index(self.index,self.corpus); self.assertFalse((self.index.parent/'.test.backup').exists()); self.assertFalse(list(self.index.parent.glob('.test.batch-*')))
 def test_evaluation_metrics_recall_no_results_and_latency(self):
  rows=[{'query_id':'q1','query':'x','expected_chunk_ids':['a','b']},{'query_id':'q2','query':'y','expected_chunk_ids':['z']}]
  result=evaluate(rows,lambda q,f,k:[{'chunk_id':'a'},{'chunk_id':'n'}] if q=='x' else [])
  self.assertEqual(result['hit_at_1'],.5); self.assertEqual(result['mrr_at_10'],.5); self.assertEqual(result['recall_at_10'],.25); self.assertEqual(result['no_result_rate'],.5); self.assertAlmostEqual(percentile([1,2,3,4],.95),3.85)
  fixture=load_queries('tests/fixtures/sec_retrieval_eval.synthetic.json'); self.assertEqual(len(fixture),2)
 def test_evaluation_schema_rejects_bad_json_and_jsonl(self):
  bad=self.local/'bad.json'; bad.write_text(json.dumps({'schema_version':'future','queries':[]}))
  with self.assertRaises(ValueError): load_queries(bad)
  row={'schema_version':EVALUATION_SCHEMA,'query_id':'q','query':'x','filters':{'form':'8-K'},'expected_chunk_ids':['c'],'expected_accession':'0000000001-24-000001','expected_section':'s','evidence_rationale':'r','label_status':'synthetic','provenance':'fixture'}; bad=self.local/'bad.jsonl'; bad.write_text(json.dumps(row)+'\n')
  with self.assertRaises(ValueError): load_queries(bad)
  row['filters']={}; row['schema_version']='future'; bad.write_text(json.dumps(row)+'\n')
  with self.assertRaises(ValueError): load_queries(bad)
 def test_output_has_no_environment_secret_or_absolute_path(self):
  os.environ['FINSIGHT_SEC_USER_AGENT']='synthetic-secret /Users/private'
  manifest=build_index(self.corpus,self.index); rendered=json.dumps(manifest)+json.dumps(search(self.index,'revenue',corpus=self.corpus))
  self.assertNotIn('synthetic-secret',rendered); self.assertNotIn('/Users/',rendered); self.assertFalse(manifest['network_executed']); self.assertEqual(manifest['model_calls'],0)

if __name__=='__main__': unittest.main()
