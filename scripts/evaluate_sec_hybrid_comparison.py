#!/usr/bin/env python3
"""Offline three-way evaluation for BM25, dense, and fixed RRF."""
import argparse,json,os,tempfile
from pathlib import Path
from finsight_rag.comparison import _category
from finsight_rag.dense_retrieval import load_dense_index,search_loaded_dense
from finsight_rag.embeddings import BGEEmbedder
from finsight_rag.evaluation import load_queries
from finsight_rag.hybrid_retrieval import enrich_results,evaluate_three_way,require_offline_environment,validate_compatible_indexes,validate_query_file
from finsight_rag.retrieval import _local_data_path,load_index,search_loaded

def main():
 p=argparse.ArgumentParser()
 for name in ("queries","bm25-index","dense-index","corpus","model-revision"):p.add_argument("--"+name,required=True)
 p.add_argument("--cache-folder",default=".local_data/models/hub");p.add_argument("--batch-size",type=int,default=32);p.add_argument("--output",required=True);p.add_argument("--overwrite",action="store_true");p.add_argument("--offline",action="store_true",required=True);a=p.parse_args()
 require_offline_environment();queries_sha256=validate_query_file(a.queries)
 rows=load_queries(a.queries);embedder=BGEEmbedder(revision=a.model_revision,batch_size=a.batch_size,cache_folder=a.cache_folder,local_files_only=True)
 bm,br,bi=load_index(a.bm25_index,a.corpus);dm,dr,di=load_dense_index(a.dense_index,a.corpus,embedder);validate_compatible_indexes(bm,br,dm,dr,embedder=embedder)
 def lexical(query,filters,depth):return enrich_results(search_loaded(bm,br,bi,query,top_k=depth,symbol=filters.get("symbol"),form=filters.get("form"),as_of=filters.get("as_of")),br)
 def semantic(query,filters,depth):return enrich_results(search_loaded_dense(dm,dr,di,query,embedder,top_k=depth,symbol=filters.get("symbol"),form=filters.get("form"),as_of=filters.get("as_of")),dr)
 provenance={"queries_sha256":queries_sha256,"query_count":len(rows),"corpus_aggregate_sha256":bm["corpus_aggregate_sha256"],"corpus_chunks_sha256":bm["corpus_chunks_sha256"],"chunk_count":bm["chunk_count"],"bm25_index_sha256":bm["index_sha256"],"dense_documents_sha256":dm["documents_sha256"],"dense_embeddings_sha256":dm["embeddings_sha256"],"model_name":dm["model_name"],"model_revision":dm["model_revision"]}
 result=evaluate_three_way(rows,lexical,semantic,_category,provenance=provenance);output=_local_data_path(a.output)
 if output.is_symlink() or (output.exists() and not output.is_file()):raise ValueError("invalid evaluation output")
 if output.exists() and not a.overwrite:raise FileExistsError("evaluation output already exists")
 output.parent.mkdir(parents=True,exist_ok=True);fd,temp_name=tempfile.mkstemp(prefix="."+output.name+".",dir=output.parent);os.close(fd)
 try:Path(temp_name).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8");os.replace(temp_name,output)
 finally:
  if os.path.exists(temp_name):os.unlink(temp_name)
 print(json.dumps({k:v for k,v in result.items() if k!="query_details"},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
