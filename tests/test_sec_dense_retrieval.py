import hashlib,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest import mock
import numpy as np
from finsight_rag.comparison import compare
from finsight_rag.dense_retrieval import build_dense_index,load_dense_index,search_dense
from finsight_rag.embeddings import BGEEmbedder,FakeEmbedder,checked_embeddings

def sha(data):return hashlib.sha256(data).hexdigest()
class DenseTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.local=Path(self.temp.name)/'.local_data'; self.corpus=self.local/'rag/corpus'; self.corpus.mkdir(parents=True); self.index=self.local/'rag/indexes/dense'; self.embedder=FakeEmbedder(16)
  self.bundle('AAA','10-K','0000000001-24-000001','2024-01-01','alpha growth risk',0)
  self.bundle('AAA','10-Q','0000000001-24-000002','2024-04-01','quarterly cash liquidity',1)
  self.bundle('BBB','10-K','0000000002-24-000001','2024-02-01','beta market competition',2)
  (self.corpus/'semiconductor-candidates-synthetic.json').write_text(json.dumps({'candidates':[{'ticker':'AAA','cik':'0000000001','company_name':'Alpha Synthetic Corp'},{'ticker':'BBB','cik':'0000000002','company_name':'Beta Synthetic Corp'}]}))
 def tearDown(self):self.temp.cleanup()
 def bundle(self,symbol,form,accession,date,text,chunk_index):
  directory=self.corpus/symbol/'filings'/accession.replace('-',''); directory.mkdir(parents=True); cik='0000000001' if symbol=='AAA' else '0000000002'; document_id=sha((symbol+accession).encode())[:24]; chunk_id=sha((document_id+text).encode())[:24]; source=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/report.htm'; raw=f'<html>{text}</html>'.encode(); raw_hash=sha(raw)
  identity={'symbol':symbol,'cik':cik,'form':form,'accession_number':accession,'document_id':document_id}; metadata={**identity,'filing_date':date,'accepted_at':date+'T12:00:00Z','published_at':date,'source_url':source,'raw_sha256':raw_hash}; section={'section_id':'s','section_title':'Risk','text':text}; document={**metadata,'input_sha256':raw_hash,'as_of':'2024-12-31T23:59:59Z','sections':[section]}; chunk={**identity,'filing_date':date,'accepted_at':metadata['accepted_at'],'source_url':source,'chunk_id':chunk_id,'chunk_index':chunk_index,'section_id':'s','section_title':'Risk','text':text,'text_sha256':sha(text.encode()),'citation':f'{symbol} | {form} | {accession} | Risk | chunk {chunk_index} | {source}'}
  (directory/'raw.bin').write_bytes(raw); (directory/'metadata.json').write_text(json.dumps(metadata)); (directory/'document.json').write_text(json.dumps(document)); (directory/'chunks.jsonl').write_text(json.dumps(chunk)+'\n'); manifest={**identity,'as_of':document['as_of'],'raw_sha256':raw_hash,'metadata_sha256':sha((directory/'metadata.json').read_bytes()),'document_sha256':sha((directory/'document.json').read_bytes()),'chunks_sha256':sha((directory/'chunks.jsonl').read_bytes()),'section_count':1,'chunk_count':1}; (directory/'ingestion-manifest.json').write_text(json.dumps(manifest))
 def rehash_manifest(self,bundle):
  manifest=json.loads((bundle/'ingestion-manifest.json').read_text());
  for name,key in [('metadata.json','metadata_sha256'),('document.json','document_sha256'),('chunks.jsonl','chunks_sha256')]:manifest[key]=sha((bundle/name).read_bytes())
  (bundle/'ingestion-manifest.json').write_text(json.dumps(manifest))
 def rehash_index(self):
  from finsight_rag.dense_retrieval import _manifest_hash
  manifest=json.loads((self.index/'manifest.json').read_text()); manifest['documents_sha256']=sha((self.index/'documents.jsonl').read_bytes()); manifest['embeddings_sha256']=sha((self.index/'embeddings.npy').read_bytes()); manifest['manifest_sha256']=_manifest_hash(manifest); (self.index/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')

 def test_fake_uses_distinct_entries_and_normalizes(self):
  docs=self.embedder.encode_documents(['alpha']); queries=self.embedder.encode_queries(['alpha']); self.assertEqual(self.embedder.document_calls,1); self.assertEqual(self.embedder.query_calls,1); self.assertFalse(np.array_equal(docs,queries)); self.assertAlmostEqual(float(np.linalg.norm(docs[0])),1.0,places=6); self.assertEqual(docs.dtype,np.float32)
 def test_checked_embedding_rejects_shape_dtype_nan_and_zero(self):
  for value in (np.ones((1,2),dtype=np.float64),np.ones((2,2),dtype=np.float32),np.array([[np.nan,0]],dtype=np.float32),np.array([[np.inf,0]],dtype=np.float32),np.zeros((1,2),dtype=np.float32)):
   with self.assertRaises(ValueError):checked_embeddings(value,2,1)
 def test_build_load_alignment_manifest_and_cosine_search(self):
  manifest=build_dense_index(self.corpus,self.index,self.embedder,batch_size=2); self.assertEqual(manifest['chunk_count'],3); self.assertEqual(manifest['text_count'],3); self.assertEqual(manifest['embedding_batch_count'],2); self.assertFalse(manifest['network_executed']); self.assertEqual(manifest['llm_calls'],0); loaded,rows,matrix=load_dense_index(self.index,self.corpus,self.embedder); self.assertEqual([r['symbol'] for r in rows],['AAA','AAA','BBB']); self.assertEqual(matrix.shape,(3,16)); self.assertEqual(loaded['model_revision'],'synthetic-1'); result=search_dense(self.index,self.corpus,'quarterly cash',self.embedder,top_k=2,symbol='AAA',form='10-Q',as_of='2024-12-31'); self.assertEqual(len(result),1); self.assertEqual(result[0]['company_name'],'Alpha Synthetic Corp'); self.assertLessEqual(len(result[0]['evidence_preview']),400); query=self.embedder.encode_queries(['quarterly cash'])[0]; expected=float(matrix[1]@query); self.assertAlmostEqual(result[0]['score'],expected,places=6)
 def test_prefilter_point_in_time_and_stable_tie(self):
  build_dense_index(self.corpus,self.index,self.embedder); self.assertEqual(search_dense(self.index,self.corpus,'cash',self.embedder,symbol='AAA',form='10-Q',as_of='2024-02-01'),[]); a=search_dense(self.index,self.corpus,'unseen',self.embedder); b=search_dense(self.index,self.corpus,'unseen',self.embedder); self.assertEqual([x['chunk_id'] for x in a],[x['chunk_id'] for x in b])
 def test_query_and_filter_validation(self):
  build_dense_index(self.corpus,self.index,self.embedder)
  for query,kwargs in [('',{}),('x'*2001,{}),('x',{'top_k':0}),('x',{'top_k':51}),('x',{'symbol':'ZZZ'}),('x',{'form':'8-K'})]:
   with self.assertRaises(ValueError):search_dense(self.index,self.corpus,query,self.embedder,**kwargs)
 def test_model_revision_dimension_and_corpus_conflict(self):
  build_dense_index(self.corpus,self.index,self.embedder); other=FakeEmbedder(16); other.model_revision='other'
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,other)
  other=FakeEmbedder(8)
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,other)
  bundle=next(self.corpus.glob('AAA/filings/*')); (bundle/'raw.bin').write_bytes(b'changed')
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,self.embedder)
 def test_artifact_hash_shape_dtype_nan_and_alignment_fail(self):
  build_dense_index(self.corpus,self.index,self.embedder); (self.index/'documents.jsonl').write_text('changed')
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,self.embedder)
  shutil.rmtree(self.index); build_dense_index(self.corpus,self.index,self.embedder); matrix=np.load(self.index/'embeddings.npy',allow_pickle=False); np.save(self.index/'embeddings.npy',matrix[:2],allow_pickle=False); self.rehash_index()
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,self.embedder)
  shutil.rmtree(self.index); build_dense_index(self.corpus,self.index,self.embedder); matrix=np.load(self.index/'embeddings.npy',allow_pickle=False).astype(np.float64); np.save(self.index/'embeddings.npy',matrix,allow_pickle=False); self.rehash_index()
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,self.embedder)
  shutil.rmtree(self.index); build_dense_index(self.corpus,self.index,self.embedder); matrix=np.load(self.index/'embeddings.npy',allow_pickle=False); matrix[0,0]=np.nan; np.save(self.index/'embeddings.npy',matrix,allow_pickle=False); self.rehash_index()
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,self.embedder)
  shutil.rmtree(self.index); build_dense_index(self.corpus,self.index,self.embedder); lines=(self.index/'documents.jsonl').read_text().splitlines(); (self.index/'documents.jsonl').write_text('\n'.join([lines[1],lines[0],*lines[2:]])+'\n'); self.rehash_index()
  with self.assertRaises(ValueError):load_dense_index(self.index,self.corpus,self.embedder)
 def test_default_skip_conflict_overwrite_and_recovery(self):
  first=build_dense_index(self.corpus,self.index,self.embedder); self.assertEqual(build_dense_index(self.corpus,self.index,self.embedder)['status'],'already_completed'); other=FakeEmbedder(8)
  with self.assertRaises(FileExistsError):build_dense_index(self.corpus,self.index,other)
  before={p.name:p.read_bytes() for p in self.index.iterdir()}; original=os.replace; calls=[0]
  def fail_second(src,dst):
   calls[0]+=1
   if calls[0]==2:raise OSError('commit failure')
   return original(src,dst)
  with mock.patch('finsight_rag.dense_retrieval.os.replace',side_effect=fail_second):
   with self.assertRaises(OSError):build_dense_index(self.corpus,self.index,self.embedder,overwrite=True,batch_size=1)
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.index.iterdir()}); load_dense_index(self.index,self.corpus,self.embedder); self.assertFalse(list(self.index.parent.glob('.dense.batch-*'))); self.assertFalse((self.index.parent/'.dense.backup').exists()); self.assertEqual(first['index_id'],json.loads((self.index/'manifest.json').read_text())['index_id'])
 def test_first_write_failure_cleans_temp(self):
  with mock.patch('finsight_rag.dense_retrieval.np.save',side_effect=OSError('write')):
   with self.assertRaises(OSError):build_dense_index(self.corpus,self.index,self.embedder)
  self.assertFalse(self.index.exists()); self.assertFalse(list(self.index.parent.glob('.dense.batch-*')))
 def test_path_traversal_and_symlink_rejected(self):
  with self.assertRaises(ValueError):build_dense_index(self.corpus,self.local/'../escape',self.embedder)
  link=self.local/'rag/indexes/link'; link.parent.mkdir(parents=True); link.symlink_to(self.corpus,target_is_directory=True)
  with self.assertRaises(ValueError):build_dense_index(self.corpus,link,self.embedder)
  with self.assertRaises(ValueError):BGEEmbedder(revision='x',cache_folder='.local_data/other',local_files_only=True)
 def test_bad_embedder_output_rejected(self):
  class Bad(FakeEmbedder):
   def encode_documents(self,texts):return np.ones((len(list(texts)),self.dimension),dtype=np.float64)
  with self.assertRaises(ValueError):build_dense_index(self.corpus,self.index,Bad(4))
 def test_comparison_metrics_and_counts(self):
  rows=[{'query_id':'amd-risk-10k','query':'a','filters':{'symbol':'AAA','form':'10-K'},'expected_chunk_ids':['x']},{'query_id':'avgo-business-10k','query':'b','filters':{'symbol':'BBB','form':'10-Q'},'expected_chunk_ids':['y']},{'query_id':'intc-segments-10q','query':'c','filters':{'symbol':'AAA','form':'10-Q'},'expected_chunk_ids':['z']}]
  def bm(q,f,k):return [{'chunk_id':'x'}] if q=='a' else [{'chunk_id':'none'}]
  def dense(q,f,k):return [{'chunk_id':'x'}] if q=='a' else ([{'chunk_id':'y'}] if q=='b' else [{'chunk_id':'none'}])
  result=compare(rows,bm,dense,network_executed=False); self.assertEqual(result['success_overlap'],{'both_success':1,'only_bm25_success':0,'only_dense_success':1,'both_failed':1}); self.assertEqual(result['bm25_misses_recovered_by_dense_count'],1); self.assertEqual(result['winner_counts'],{'dense_improved':1,'tie':2,'dense_declined':0}); self.assertIn('risk',result['by_category']); self.assertFalse(result['network_executed']); self.assertEqual(result['llm_calls'],0)
  with self.assertRaises(ValueError):compare(rows,bm,dense)
 def test_offline_audit_and_private_output(self):
  online=FakeEmbedder(4); online.network_executed=None
  with self.assertRaises(ValueError):build_dense_index(self.corpus,self.index,online)
  build_dense_index(self.corpus,self.index,self.embedder); result=search_dense(self.index,self.corpus,'cash',self.embedder)
  rendered=json.dumps(result); self.assertNotIn(str(Path.cwd()),rendered); self.assertNotIn('FINSIGHT_SEC_USER_AGENT',rendered); self.assertNotRegex(rendered,r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')

if __name__=='__main__':unittest.main()
