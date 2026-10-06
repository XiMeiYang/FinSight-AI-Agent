#!/usr/bin/env python3
import argparse,json
from finsight_rag.evaluation import load_queries
from finsight_rag.comparison import compare
from finsight_rag.retrieval import load_index,search_loaded
from finsight_rag.embeddings import BGEEmbedder
from finsight_rag.dense_retrieval import load_dense_index,search_loaded_dense
p=argparse.ArgumentParser(); p.add_argument('--queries',required=True); p.add_argument('--bm25-index',required=True); p.add_argument('--dense-index',required=True); p.add_argument('--corpus',required=True); p.add_argument('--model-revision',required=True); p.add_argument('--batch-size',type=int,default=32); p.add_argument('--cache-folder',default='.local_data/models/hub'); p.add_argument('--offline',action='store_true',required=True); a=p.parse_args(); rows=load_queries(a.queries); e=BGEEmbedder(revision=a.model_revision,batch_size=a.batch_size,cache_folder=a.cache_folder,local_files_only=a.offline); bm,bdocs,bindex=load_index(a.bm25_index,a.corpus); dm,ddocs,dindex=load_dense_index(a.dense_index,a.corpus,e)
def b(q,f,k): return search_loaded(bm,bdocs,bindex,q,top_k=k,symbol=f.get('symbol'),form=f.get('form'),as_of=f.get('as_of'))
def d(q,f,k): return search_loaded_dense(dm,ddocs,dindex,q,e,top_k=k,symbol=f.get('symbol'),form=f.get('form'),as_of=f.get('as_of'))
print(json.dumps(compare(rows,b,d,network_executed=e.network_executed),ensure_ascii=False,sort_keys=True))
