"""Same-query diagnostic comparison for lexical and dense retrieval."""
from __future__ import annotations
from collections import defaultdict
from .evaluation import evaluate
_CATEGORIES={
 "amd-business-10k":"business","amd-risk-10k":"risk","amd-inventory-10q":"financial_fact","amd-margin-10q":"mda",
 "avgo-business-10k":"business","avgo-supply-risk-10k":"risk","avgo-eps-10q":"financial_fact","avgo-ai-platform-10q":"mda",
 "intc-manufacturing-10k":"business","intc-competition-10k":"risk","intc-segments-10q":"segment","intc-apollo-10q":"mda",
 "nvda-business-10k":"business","nvda-supply-risk-10k":"risk","nvda-cash-flow-10q":"financial_fact","nvda-supply-commitments-10q":"mda",
 "qcom-business-10k":"business","qcom-china-risk-10k":"risk","qcom-qct-revenue-10q":"financial_fact","qcom-revenue-change-10q":"mda",
}
def _category(row):
 try:return _CATEGORIES[row["query_id"]]
 except KeyError as exc:raise ValueError("query category is not explicitly classified") from exc
def _summary(items,key):
 ranks=[item[key] for item in items]; count=len(ranks)
 return {"query_count":count,"hit_at_1":sum(x==1 for x in ranks)/count,"hit_at_10":sum(x is not None and x<=10 for x in ranks)/count,"mrr_at_10":sum(0 if x is None or x>10 else 1/x for x in ranks)/count}
def compare(rows,bm25_search,dense_search,*,network_executed=None):
 if network_executed is not False: raise ValueError("offline evaluation is required")
 if len({row["query_id"] for row in rows})!=len(rows): raise ValueError("duplicate query id")
 bm25=evaluate(rows,bm25_search); dense=evaluate(rows,dense_search); details=[]
 for row,bm,dm in zip(rows,bm25["queries"],dense["queries"]):
  br= bm["first_relevant_rank"]; dr=dm["first_relevant_rank"]
  if dr is not None and (br is None or dr<br): winner="dense"
  elif br is not None and (dr is None or br<dr): winner="bm25"
  else: winner="tie"
  details.append({"query_id":row["query_id"],"symbol":row["filters"].get("symbol"),"form":row["filters"].get("form"),"category":_category(row),"bm25_rank":br,"dense_rank":dr,"winner":winner})
 both=sum(x["bm25_rank"] is not None and x["dense_rank"] is not None for x in details); only_bm25=sum(x["bm25_rank"] is not None and x["dense_rank"] is None for x in details); only_dense=sum(x["bm25_rank"] is None and x["dense_rank"] is not None for x in details); neither=len(details)-both-only_bm25-only_dense
 grouped={}
 for label,field in (("by_category","category"),("by_form","form"),("by_company","symbol")):
  buckets=defaultdict(list)
  for item in details:buckets[item[field]].append(item)
  grouped[label]={name:{"bm25":_summary(values,"bm25_rank"),"dense":_summary(values,"dense_rank")} for name,values in sorted(buckets.items())}
 recovered=[x["query_id"] for x in details if x["bm25_rank"] is None and x["dense_rank"] is not None]
 return {"status":"completed","network_executed":network_executed,"llm_calls":0,"bm25":bm25,"dense":dense,"winner_counts":{"dense_improved":sum(x["winner"]=="dense" for x in details),"tie":sum(x["winner"]=="tie" for x in details),"dense_declined":sum(x["winner"]=="bm25" for x in details)},"success_overlap":{"both_success":both,"only_bm25_success":only_bm25,"only_dense_success":only_dense,"both_failed":neither},"bm25_top10_failure_count":sum(x["bm25_rank"] is None for x in details),"bm25_misses_recovered_by_dense_count":len(recovered),"bm25_misses_recovered_by_dense":recovered,**grouped,"query_comparison":details}
