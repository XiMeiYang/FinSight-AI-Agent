#!/usr/bin/env python3
import argparse, json
from finsight_rag.embeddings import BGEEmbedder
from finsight_rag.retrieval import load_index
from finsight_rag.dense_retrieval import load_dense_index
from finsight_rag.hybrid_retrieval import require_offline_environment,search_loaded_hybrid

p=argparse.ArgumentParser(); p.add_argument('--bm25-index',required=True); p.add_argument('--dense-index',required=True); p.add_argument('--corpus',required=True); p.add_argument('--query',required=True); p.add_argument('--top-k',type=int,default=10); p.add_argument('--symbol'); p.add_argument('--form'); p.add_argument('--as-of'); p.add_argument('--model-revision',required=True); p.add_argument('--batch-size',type=int,default=32); p.add_argument('--cache-folder',default='.local_data/models/hub'); p.add_argument('--offline',action='store_true',required=True); a=p.parse_args()
require_offline_environment()
e=BGEEmbedder(revision=a.model_revision,batch_size=a.batch_size,cache_folder=a.cache_folder,local_files_only=True); bm,br,bi=load_index(a.bm25_index,a.corpus); dm,dr,di=load_dense_index(a.dense_index,a.corpus,e)
print(json.dumps(search_loaded_hybrid(bm,br,bi,dm,dr,di,e,a.query,top_k=a.top_k,symbol=a.symbol,form=a.form,as_of=a.as_of),ensure_ascii=False,sort_keys=True))
