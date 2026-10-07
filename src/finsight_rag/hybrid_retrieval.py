"""Strict, offline reciprocal-rank fusion for local SEC indexes."""
from __future__ import annotations
import hashlib
import os
import statistics
import time
from collections import defaultdict
from .dense_retrieval import search_loaded_dense
from .evaluation import percentile
from .retrieval import _local_data_path,search_loaded,TOKENIZER_VERSION

RRF_DEPTH=50
RRF_K=60
RRF_WEIGHTS={"bm25":1,"dense":1}
RRF_SCHEMA="sec-hybrid-rrf-1.0"
FROZEN_QUERY_SHA256="2e66af31ba0ef46da30575351d25df9009ce1b7192ee123745b1bf0c2944ca69"
_IDENTITY=("symbol","company_name","cik","form","accession_number","document_id","filing_date","accepted_at","published_at","section_id","section_title","chunk_index","source_url","corpus_as_of","text")

def _identity(manifest, rows):
    ids=[x.get("chunk_id") for x in rows]
    if len(set(ids)) != len(ids): raise ValueError("duplicate chunk_id in index")
    return {"provenance":tuple(manifest.get(x) for x in ("corpus_aggregate_sha256","corpus_chunks_sha256","indexed_documents_sha256")),"rows":{x.get("chunk_id"):tuple(x.get(k) for k in _IDENTITY) for x in rows}}

def require_offline_environment(environ=None):
    environ=os.environ if environ is None else environ
    for key in ("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","HF_HUB_DISABLE_TELEMETRY"):
        if environ.get(key)!="1":raise ValueError(f"{key}=1 is required")

def validate_query_file(path,expected_sha256=FROZEN_QUERY_SHA256):
    path=_local_data_path(path,True)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=expected_sha256:raise ValueError("frozen query SHA-256 mismatch")
    return digest

def validate_compatible_indexes(bm25_manifest,bm25_rows,dense_manifest,dense_rows,*,embedder=None,offline=True):
    if offline is not True: raise ValueError("offline hybrid retrieval is required")
    if _identity(bm25_manifest,bm25_rows) != _identity(dense_manifest,dense_rows): raise ValueError("BM25 and dense corpus, universe, identity, text, or as_of mismatch")
    if bm25_manifest.get("tokenizer_version") != TOKENIZER_VERSION: raise ValueError("BM25 tokenizer mismatch")
    if dense_manifest.get("tokenizer_version") is not None and dense_manifest.get("tokenizer_version") != TOKENIZER_VERSION: raise ValueError("dense tokenizer mismatch")
    if embedder is not None and (dense_manifest.get("model_name") != embedder.model_name or dense_manifest.get("model_revision") != embedder.model_revision): raise ValueError("dense model provenance mismatch")
    if bm25_manifest.get("network_executed") is not False or dense_manifest.get("network_executed") is not False or (embedder is not None and getattr(embedder,"network_executed",None) is not False): raise ValueError("offline provenance required")

def _key(x): return (x.get("symbol",""),x.get("accession_number",""),x.get("section_id",x.get("section","")),x.get("chunk_index",0),x.get("chunk_id",""))
def _check(results):
    seen=set()
    for pos,item in enumerate(results[:RRF_DEPTH],1):
        if item.get("chunk_id") in seen or not item.get("chunk_id"): raise ValueError("duplicate or missing chunk_id")
        if item.get("rank",pos) != pos: raise ValueError("retrieval ranks must be continuous 1-based")
        seen.add(item["chunk_id"])

def enrich_results(results, rows):
    """Attach stable index identity without exposing full indexed text."""
    catalog={row["chunk_id"]:row for row in rows}
    enriched=[]
    for item in results:
        source=catalog.get(item.get("chunk_id"))
        if source is None: raise ValueError("retrieval result is outside the index universe")
        copy=dict(item)
        for key in ("document_id","section_id"):
            copy[key]=source.get(key)
        for key in ("symbol","company_name","cik","form","accession_number","filing_date","accepted_at","published_at","chunk_index","source_url","corpus_as_of"):
            if copy.get(key)!=source.get(key): raise ValueError("retrieval result identity mismatch")
        if copy.get("evidence_preview") != source["text"][:400]: raise ValueError("retrieval result text mismatch")
        enriched.append(copy)
    return enriched

def fuse_results(bm25_results,dense_results,*,top_k=10,rrf_k=RRF_K):
    if not isinstance(top_k,int) or not 1<=top_k<=50: raise ValueError("top_k must be between 1 and 50")
    if rrf_k != RRF_K: raise ValueError("RRF k is fixed at 60")
    _check(bm25_results); _check(dense_results); merged={}
    for source,results in (("bm25",bm25_results[:RRF_DEPTH]),("dense",dense_results[:RRF_DEPTH])):
        for pos,item in enumerate(results,1):
            cid=item["chunk_id"]; row=merged.setdefault(cid,{k:v for k,v in item.items() if k not in ("rank","score","evidence_preview")})
            row.setdefault("section_id", item.get("section_id", item.get("section")))
            for key in ("symbol","company_name","cik","form","accession_number","document_id","filing_date","accepted_at","published_at","section_id","chunk_index","source_url","corpus_as_of"):
                incoming = item.get("section_id", item.get("section")) if key == "section_id" else item.get(key)
                if row.get(key) is not None and incoming is not None and row.get(key) != incoming: raise ValueError("conflicting result identity")
            row[f"{source}_rank"]=pos; row[f"{source}_score"]=item.get("score"); row["rrf_score"]=row.get("rrf_score",0.0)+RRF_WEIGHTS[source]/(RRF_K+pos); row["evidence_preview"]=item.get("evidence_preview","")[:400]
    for row in merged.values():
        row["retrieved_by"]="both" if row.get("bm25_rank") is not None and row.get("dense_rank") is not None else ("bm25" if row.get("bm25_rank") is not None else "dense"); row["source_composition"]=row["retrieved_by"]; row["best_rank"]=min(x for x in (row.get("bm25_rank"),row.get("dense_rank")) if x is not None)
        for key in ("bm25_rank","dense_rank","bm25_score","dense_score"): row.setdefault(key,None)
    ranked=sorted(merged.values(),key=lambda x:(-x["rrf_score"],0 if x["retrieved_by"]=="both" else 1,x["best_rank"],*_key(x)))
    for rank,row in enumerate(ranked[:top_k],1): row.update(rank=rank,rrf_k=RRF_K,rrf_depth=RRF_DEPTH)
    return ranked[:top_k]

def search_loaded_hybrid(bm25_manifest,bm25_rows,bm25_index,dense_manifest,dense_rows,dense_matrix,embedder,query,*,top_k=10,symbol=None,form=None,as_of=None):
    validate_compatible_indexes(bm25_manifest,bm25_rows,dense_manifest,dense_rows,embedder=embedder)
    start=time.perf_counter(); b=enrich_results(search_loaded(bm25_manifest,bm25_rows,bm25_index,query,top_k=RRF_DEPTH,symbol=symbol,form=form,as_of=as_of),bm25_rows); d=enrich_results(search_loaded_dense(dense_manifest,dense_rows,dense_matrix,query,embedder,top_k=RRF_DEPTH,symbol=symbol,form=form,as_of=as_of),dense_rows); fused=fuse_results(b,d,top_k=top_k)
    return {"schema_version":RRF_SCHEMA,"status":"completed","network_executed":False,"llm_calls":0,"filters":{"symbol":symbol,"form":form,"as_of":as_of},"rrf":{"depth":RRF_DEPTH,"k":RRF_K,"weights":RRF_WEIGHTS},"timing_ms":{"hybrid_end_to_end":(time.perf_counter()-start)*1000},"results":fused}

def search_hybrid(*args,**kwargs): return search_loaded_hybrid(*args,**kwargs)

def _first_rank(results, expected):
    return next((position for position,item in enumerate(results,1) if item.get("chunk_id") in expected),None)

def _metric_summary(ranks,no_results,latencies):
    total=len(ranks)
    return {**{f"hit_at_{k}":sum(rank is not None and rank<=k for rank in ranks)/total for k in (1,3,5,10)},
            "mrr_at_10":sum(0 if rank is None or rank>10 else 1/rank for rank in ranks)/total,
            "recall_at_10":sum(rank is not None and rank<=10 for rank in ranks)/total,
            "no_result_rate":no_results/total,"median_latency_ms":statistics.median(latencies),"p95_latency_ms":percentile(latencies,.95)}

def _relative(details,left,right):
    counts={"improved":0,"tie":0,"declined":0}
    for detail in details:
        a=detail["ranks"][left]; b=detail["ranks"][right]
        a=a if a is not None and a<=10 else None; b=b if b is not None and b<=10 else None
        if a is not None and (b is None or a<b): counts["improved"]+=1
        elif b is not None and (a is None or b<a): counts["declined"]+=1
        else: counts["tie"]+=1
    return counts

def _group_summary(ranks):
    total=len(ranks)
    return {**{f"hit_at_{k}":sum(rank is not None and rank<=k for rank in ranks)/total for k in (1,3,5,10)},
            "mrr_at_10":sum(0 if rank is None or rank>10 else 1/rank for rank in ranks)/total,
            "recall_at_10":sum(rank is not None and rank<=10 for rank in ranks)/total}

def evaluate_three_way(query_rows,bm25_search,dense_search,category,*,provenance,clock=time.perf_counter):
    """Evaluate frozen queries; search callables receive identical filters and depth."""
    required=("queries_sha256","corpus_aggregate_sha256","bm25_index_sha256","dense_documents_sha256","dense_embeddings_sha256","model_name","model_revision")
    if any(not provenance.get(key) for key in required):raise ValueError("complete evaluation provenance is required")
    ranks={name:[] for name in ("bm25","dense","hybrid")}; no_results={name:0 for name in ranks}
    latency={name:[] for name in ("bm25_end_to_end_ms","dense_end_to_end_ms","rrf_ms","hybrid_end_to_end_ms")}; details=[]
    for row in query_rows:
        filters=dict(row.get("filters") or {}); expected=set(row["expected_chunk_ids"])
        start=clock(); bm25=bm25_search(row["query"],filters,RRF_DEPTH); bm_ms=(clock()-start)*1000
        start=clock(); dense=dense_search(row["query"],filters,RRF_DEPTH); dense_ms=(clock()-start)*1000
        start=clock(); hybrid=fuse_results(bm25,dense,top_k=RRF_DEPTH); rrf_ms=(clock()-start)*1000
        latency["bm25_end_to_end_ms"].append(bm_ms); latency["dense_end_to_end_ms"].append(dense_ms); latency["rrf_ms"].append(rrf_ms); latency["hybrid_end_to_end_ms"].append(bm_ms+dense_ms+rrf_ms)
        query_ranks={name:_first_rank(result,expected) for name,result in (("bm25",bm25),("dense",dense),("hybrid",hybrid))}
        for name,result in (("bm25",bm25),("dense",dense),("hybrid",hybrid)):
            ranks[name].append(query_ranks[name]); no_results[name]+=not bool(result)
        details.append({"query_id":row["query_id"],"symbol":filters.get("symbol"),"form":filters.get("form"),"category":category(row),"expected_chunk_ids":row["expected_chunk_ids"],"ranks":query_ranks,"top10_hits":{name:rank is not None and rank<=10 for name,rank in query_ranks.items()},"hybrid_top10_source_composition":[{"chunk_id":item["chunk_id"],"retrieved_by":item["retrieved_by"],"bm25_rank":item["bm25_rank"],"dense_rank":item["dense_rank"]} for item in hybrid[:10]]})
    latency_summary={name:{"samples_ms":values,"median_ms":statistics.median(values),"p95_ms":percentile(values,.95)} for name,values in latency.items()}
    metrics={name:_metric_summary(values,no_results[name],latency["hybrid_end_to_end_ms" if name=="hybrid" else name+"_end_to_end_ms"]) for name,values in ranks.items()}
    top10=lambda detail,name:detail["top10_hits"][name]
    only_bm25=[d["query_id"] for d in details if top10(d,"bm25") and not top10(d,"dense")]
    only_dense=[d["query_id"] for d in details if top10(d,"dense") and not top10(d,"bm25")]
    grouped={}
    for field,label in (("category","by_category"),("form","by_form"),("symbol","by_company")):
        buckets=defaultdict(list)
        for detail in details:buckets[detail[field]].append(detail)
        grouped[label]={key:{name:_group_summary([x["ranks"][name] for x in values]) for name in ranks} for key,values in sorted(buckets.items())}
    return {"schema_version":"sec-hybrid-eval-1.0","status":"completed","network_executed":False,"llm_calls":0,"provenance":dict(provenance),"rrf":{"depth":RRF_DEPTH,"k":RRF_K,"weights":RRF_WEIGHTS},"metrics":metrics,
            "hybrid_vs_bm25":_relative(details,"hybrid","bm25"),"hybrid_vs_dense":_relative(details,"hybrid","dense"),
            "bm25_failures_recovered_by_hybrid_count":sum(not top10(d,"bm25") and top10(d,"hybrid") for d in details),"dense_failures_recovered_by_hybrid_count":sum(not top10(d,"dense") and top10(d,"hybrid") for d in details),
            "bm25_only_query_ids":only_bm25,"bm25_only_preserved_count":sum(top10(d,"hybrid") for d in details if d["query_id"] in only_bm25),"bm25_only_lost_query_ids":[d["query_id"] for d in details if d["query_id"] in only_bm25 and not top10(d,"hybrid")],
            "dense_only_query_ids":only_dense,"dense_only_recovered_count":sum(top10(d,"hybrid") for d in details if d["query_id"] in only_dense),"dense_only_lost_query_ids":[d["query_id"] for d in details if d["query_id"] in only_dense and not top10(d,"hybrid")],
            "three_way_success":{"all_three_success":sum(all(d["top10_hits"].values()) for d in details),"only_hybrid_success":sum(top10(d,"hybrid") and not top10(d,"bm25") and not top10(d,"dense") for d in details),"hybrid_failed":sum(not top10(d,"hybrid") for d in details),"all_three_failed":sum(not any(d["top10_hits"].values()) for d in details)},
            **grouped,"latency_ms":latency_summary,"latency_note":"model and indexes preloaded; process startup, model load, and download excluded; dense query embedding and similarity are not reliably separated","query_details":details}
