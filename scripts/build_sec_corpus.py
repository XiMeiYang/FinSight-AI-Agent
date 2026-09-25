#!/usr/bin/env python3
"""Create candidate/coverage manifests; network mode is explicit and gated."""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from finsight_rag.catalog import SecurityCatalog
TARGETS=('NVDA','AMD','INTC','AVGO','QCOM')
def main():
 p=argparse.ArgumentParser(); p.add_argument('--ticker-mapping',required=True); p.add_argument('--submissions-dir',required=True); p.add_argument('--output',required=True); p.add_argument('--network',action='store_true'); p.add_argument('--max-10k',type=int,default=5); p.add_argument('--max-10q',type=int,default=15); a=p.parse_args()
 if a.network and not os.getenv('FINSIGHT_SEC_USER_AGENT'): raise SystemExit('FINSIGHT_SEC_USER_AGENT is required for network mode')
 catalog=SecurityCatalog.from_json(a.ticker_mapping); root=Path(a.submissions_dir); rows=[]
 for ticker in TARGETS:
  try: rec=catalog.resolve(ticker)
  except Exception as e: rows.append({'ticker':ticker,'status':'unavailable','reason':'ticker mapping unavailable'}); continue
  matches=[]; files=list(root.glob(f'*{rec["cik"]}*json'))
  for f in files:
   try: payload=json.loads(f.read_text(encoding='utf-8'))
   except Exception: continue
   recent=payload.get('filings',{}).get('recent',{}); n=len(recent.get('form',[]))
   for i in range(n):
    form=str(recent['form'][i]).strip().upper()
    if form in ('10-K','10-Q'):
     matches.append({'form':form,'filing_date':recent.get('filingDate',[None]*n)[i],'accession_number':recent.get('accessionNumber',[None]*n)[i],'primary_document':recent.get('primaryDocument',[None]*n)[i]})
  matches.sort(key=lambda x:(x['filing_date'] or '',x['accession_number'] or ''),reverse=True)
  selected=[x for x in matches if x['form']=='10-K'][:a.max_10k]+[x for x in matches if x['form']=='10-Q'][:a.max_10q]
  rows.append({'ticker':ticker,'cik':rec['cik'],'company_name':rec.get('company_name'),'available_candidates':len(matches),'selected_count':len(selected),'selected':selected,'status':'candidate_only' if not a.network else 'network_not_implemented'})
 out={'schema_version':'1.0','network_executed':False,'targets':TARGETS,'limits':{'10-K':a.max_10k,'10-Q':a.max_10q},'candidates':rows}
 Path(a.output).write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8')
 print(json.dumps({'network_executed':False,'targets':rows},ensure_ascii=False))
if __name__=='__main__': main()
