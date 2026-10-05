#!/usr/bin/env python3
import argparse,json
from finsight_rag.retrieval import build_index
p=argparse.ArgumentParser(); p.add_argument('--corpus',required=True); p.add_argument('--output',required=True); p.add_argument('--overwrite',action='store_true'); p.add_argument('--k1',type=float,default=1.5); p.add_argument('--b',type=float,default=.75)
a=p.parse_args(); print(json.dumps(build_index(a.corpus,a.output,overwrite=a.overwrite,k1=a.k1,b=a.b),sort_keys=True))
