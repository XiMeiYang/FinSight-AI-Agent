#!/usr/bin/env python3
import argparse,json
from finsight_rag.evaluation import load_queries,evaluate
from finsight_rag.retrieval import load_index,search_loaded
p=argparse.ArgumentParser(); p.add_argument('--index',required=True); p.add_argument('--queries',required=True); p.add_argument('--corpus'); a=p.parse_args(); rows=load_queries(a.queries); manifest,documents,bm25=load_index(a.index,a.corpus)
def run(q,f,k): return search_loaded(manifest,documents,bm25,q,top_k=k,symbol=f.get('symbol'),form=f.get('form'),as_of=f.get('as_of'))
print(json.dumps({'status':'completed','network_executed':False,'model_calls':0,**evaluate(rows,run)},sort_keys=True))
