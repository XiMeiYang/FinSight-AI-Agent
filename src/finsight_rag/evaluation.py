"""Deterministic metrics and validation for offline retrieval evaluation."""
from __future__ import annotations
import json,re,statistics,time
from pathlib import Path

EVALUATION_SCHEMA="sec-retrieval-eval-1.0"
REQUIRED=("query_id","query","filters","expected_chunk_ids","expected_accession","expected_section","evidence_rationale","label_status","provenance")

def load_queries(path):
 path=Path(path)
 if path.suffix==".jsonl":
  rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
  if any(not isinstance(row,dict) or row.get("schema_version")!=EVALUATION_SCHEMA for row in rows): raise ValueError("incompatible evaluation schema")
 else:
  payload=json.loads(path.read_text(encoding="utf-8"))
  if not isinstance(payload,dict) or payload.get("schema_version")!=EVALUATION_SCHEMA: raise ValueError("incompatible evaluation schema")
  rows=payload.get("queries")
 if not isinstance(rows,list) or not rows: raise ValueError("query set must be a non-empty list")
 seen=set()
 for row in rows:
  if not isinstance(row,dict) or any(key not in row for key in REQUIRED): raise ValueError("invalid query row")
  if not isinstance(row["query_id"],str) or not row["query_id"] or row["query_id"] in seen: raise ValueError("duplicate or invalid query_id")
  seen.add(row["query_id"])
  if not isinstance(row["query"],str) or not row["query"].strip(): raise ValueError("query text required")
  if not isinstance(row["filters"],dict) or set(row["filters"])-{"symbol","form","as_of"}: raise ValueError("invalid filters")
  if row["filters"].get("form") not in (None,"10-K","10-Q"): raise ValueError("invalid form filter")
  if not isinstance(row["expected_chunk_ids"],list) or not row["expected_chunk_ids"] or any(not isinstance(x,str) or not x for x in row["expected_chunk_ids"]): raise ValueError("expected evidence required")
  if not isinstance(row["expected_accession"],str) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}",row["expected_accession"]): raise ValueError("invalid expected accession")
  for key in ("expected_section","evidence_rationale","label_status","provenance"):
   if not isinstance(row[key],str) or not row[key].strip(): raise ValueError(f"invalid {key}")
 return rows

def percentile(values,q):
 ordered=sorted(values)
 if not ordered:return 0.0
 position=(len(ordered)-1)*q; lower=int(position); upper=min(lower+1,len(ordered)-1)
 return ordered[lower]+(ordered[upper]-ordered[lower])*(position-lower)

def evaluate(rows,searcher):
 if not rows: raise ValueError("evaluation rows required")
 hits={1:0,3:0,5:0,10:0}; reciprocal=[]; recalls=[]; latencies=[]; no_results=0; failures=[]; details=[]
 for row in rows:
  start=time.perf_counter()
  try: output=searcher(row["query"],row.get("filters") or {},10)
  except Exception as exc:
   output=[]; failures.append({"query_id":row["query_id"],"error_type":type(exc).__name__})
  latencies.append((time.perf_counter()-start)*1000)
  if not output: no_results+=1
  ids=[item.get("chunk_id") for item in output]; expected=set(row["expected_chunk_ids"]); ranks=[i+1 for i,value in enumerate(ids[:10]) if value in expected]; first=min(ranks) if ranks else None
  reciprocal.append(0.0 if first is None else 1.0/first); recalls.append(len(expected.intersection(ids[:10]))/len(expected))
  for k in hits:
   if expected.intersection(ids[:k]): hits[k]+=1
  details.append({"query_id":row["query_id"],"first_relevant_rank":first,"retrieved_count":len(output),"relevant_retrieved_at_10":len(expected.intersection(ids[:10]))})
 count=len(rows)
 return {"query_count":count,"hit_at_1":hits[1]/count,"hit_at_3":hits[3]/count,"hit_at_5":hits[5]/count,"hit_at_10":hits[10]/count,"mrr_at_10":sum(reciprocal)/count,"recall_at_10":sum(recalls)/count,"no_result_rate":no_results/count,"median_latency_ms":statistics.median(latencies),"p95_latency_ms":percentile(latencies,.95),"failed_query_count":len(failures),"failures":failures,"queries":details}
