#!/usr/bin/env python3
import argparse,json
from finsight_rag.embeddings import BGEEmbedder
from finsight_rag.dense_retrieval import build_dense_index
p=argparse.ArgumentParser(); p.add_argument('--corpus',required=True); p.add_argument('--output',required=True); p.add_argument('--model-name',default='BAAI/bge-small-en-v1.5'); p.add_argument('--model-revision',required=True); p.add_argument('--batch-size',type=int,default=32); p.add_argument('--cache-folder',default='.local_data/models/hub'); p.add_argument('--offline',action='store_true',required=True); p.add_argument('--overwrite',action='store_true'); a=p.parse_args()
e=BGEEmbedder(a.model_name,a.model_revision,a.batch_size,a.cache_folder,local_files_only=a.offline); print(json.dumps(build_dense_index(a.corpus,a.output,e,batch_size=a.batch_size,overwrite=a.overwrite),sort_keys=True))
