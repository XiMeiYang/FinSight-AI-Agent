#!/usr/bin/env python3
import argparse,json
from finsight_rag.retrieval import search
p=argparse.ArgumentParser(); p.add_argument('--index',required=True); p.add_argument('--corpus'); p.add_argument('--query',required=True); p.add_argument('--top-k',type=int,default=10); p.add_argument('--symbol'); p.add_argument('--form'); p.add_argument('--as-of'); a=p.parse_args()
print(json.dumps({'status':'completed','network_executed':False,'model_calls':0,'results':search(a.index,a.query,top_k=a.top_k,symbol=a.symbol,form=a.form,as_of=a.as_of,corpus=a.corpus)},ensure_ascii=False,sort_keys=True))
