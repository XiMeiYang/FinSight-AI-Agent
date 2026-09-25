#!/usr/bin/env python3
"""Candidate inventory and explicitly gated SEC primary-document downloader."""
from __future__ import annotations
import argparse,json,os,sys,hashlib
from pathlib import Path
from finsight_rag.catalog import SecurityCatalog
from finsight_rag.ingestion import parse_time
from finsight_sec import SECClient, SECConfig
from urllib.parse import urlparse
TARGETS=('NVDA','AMD','INTC','AVGO','QCOM')
FORMS=('10-K','10-Q')
def _url(cik,acc,doc): return f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/{doc}'
def _rows(payload,rec):
 recent=payload.get('filings',{}).get('recent',{}); n=len(recent.get('form',[])); out=[]
 for i in range(n):
  form=str(recent['form'][i] or '').strip().upper(); acc=recent.get('accessionNumber',[None]*n)[i]; doc=recent.get('primaryDocument',[None]*n)[i]
  if form not in FORMS or not acc or not doc: continue
  if not isinstance(acc,str) or len(acc)!=18 or acc[10]!='-': continue
  fd=recent.get('filingDate',[None]*n)[i]; rd=recent.get('reportDate',[None]*n)[i]; ad=recent.get('acceptanceDateTime',[None]*n)[i]
  out.append({'ticker':rec['ticker'],'cik':rec['cik'],'form':form,'filing_date':fd,'report_date':rd,'acceptance_datetime':ad,'accession_number':acc,'primary_document':doc,'source_url':_url(rec['cik'],acc,doc)})
 return out
def inventory(catalog,submissions_dir,symbols,as_of,max10k,max10q):
 rows=[]; root=Path(submissions_dir); cutoff=parse_time(as_of,date_only_end=True); seen=set()
 for ticker in symbols:
  try: rec=catalog.resolve(ticker)
  except Exception: rows.append({'ticker':ticker,'status':'invalid_identity'}); continue
  files=list(root.glob(f'*{rec["cik"]}*json')); allrows=[]
  for f in files:
   try: allrows.extend(_rows(json.loads(f.read_text()),rec))
   except Exception: continue
  stats={'available_10k':0,'available_10q':0,'selected_10k':0,'selected_10q':0,'duplicates':0,'after_as_of':0,'missing_primary_document':0,'invalid_identity':0}
  if not files: rows.append({'ticker':ticker,'cik':rec['cik'],'company_name':rec.get('company_name'),'status':'missing_submissions','stats':stats,'selected':[]}); continue
  unique=[]
  for x in allrows:
   if x['accession_number'] in seen or any(y['accession_number']==x['accession_number'] for y in unique): stats['duplicates']+=1; continue
   try: t=parse_time(x['acceptance_datetime'] or x['filing_date'],date_only_end=True)
   except ValueError: stats['invalid_identity']+=1; continue
   if t>cutoff: stats['after_as_of']+=1; continue
   seen.add(x['accession_number']); unique.append(x)
  stats['available_10k']=sum(x['form']=='10-K' for x in unique); stats['available_10q']=sum(x['form']=='10-Q' for x in unique)
  unique.sort(key=lambda x:(x['filing_date'] or '',x['accession_number']),reverse=True); sel=[x for x in unique if x['form']=='10-K'][:max10k]+[x for x in unique if x['form']=='10-Q'][:max10q]; stats['selected_10k']=sum(x['form']=='10-K' for x in sel); stats['selected_10q']=sum(x['form']=='10-Q' for x in sel)
  rows.append({'ticker':ticker,'cik':rec['cik'],'company_name':rec.get('company_name'),'status':'candidate_only','stats':stats,'selected':sel})
 return rows
def download_selected(selected, output_root, user_agent, max_documents=100, max_file_bytes=50*1024*1024, max_total_bytes=500*1024*1024):
    if not user_agent or '@' not in user_agent: raise ValueError('FINSIGHT_SEC_USER_AGENT is required')
    client=SECClient(SECConfig(user_agent=user_agent)); total=0; stats={'request_count':0,'retry_count':0,'redirect_count':0,'rate_limit_count':0,'timeout_count':0,'downloaded_bytes':0,'failed_documents':[]}
    for row in selected[:max_documents]:
        u=row['source_url']; parsed=urlparse(u)
        if parsed.scheme!='https' or parsed.hostname!='www.sec.gov' or not parsed.path.startswith('/Archives/edgar/data/') or parsed.username or parsed.port not in (None,443): raise ValueError('unsafe SEC filing URL')
        try:
            raw,digest=client.download_raw(u)
            if len(raw)>max_file_bytes or total+len(raw)>max_total_bytes: raise ValueError('download budget exceeded')
            total+=len(raw); stats['downloaded_bytes']=total
            stats['request_count']=sum(x.get('attempt_count',0) for x in client.request_metadata); stats['retry_count']=sum(x.get('retry_count',0) for x in client.request_metadata)
        except Exception as exc: stats['failed_documents'].append({'accession_number':row.get('accession_number'),'error':type(exc).__name__})
    return stats

def main():
 p=argparse.ArgumentParser(); p.add_argument('--ticker-mapping',required=True); p.add_argument('--submissions-dir',required=True); p.add_argument('--output',required=True); p.add_argument('--as-of',default='2026-09-18T23:59:59Z'); p.add_argument('--symbols',default=','.join(TARGETS)); p.add_argument('--candidate-only',action='store_true'); p.add_argument('--network',action='store_true'); p.add_argument('--max-10k',type=int,default=5); p.add_argument('--max-10q',type=int,default=15); p.add_argument('--max-documents',type=int,default=100); a=p.parse_args()
 if a.network and not os.getenv('FINSIGHT_SEC_USER_AGENT'): raise SystemExit('FINSIGHT_SEC_USER_AGENT is required for network mode')
 if a.network: raise SystemExit('network download is intentionally gated until candidate manifest review')
 if not a.candidate_only and a.network is False: a.candidate_only=True
 rows=inventory(SecurityCatalog.from_json(a.ticker_mapping),a.submissions_dir,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],a.as_of,a.max_10k,a.max_10q); out={'corpus_id':'semiconductor-peer-corpus','as_of':a.as_of,'symbols':[r['ticker'] for r in rows],'company_count':len(rows),'document_count':sum(len(r.get('selected',[])) for r in rows),'section_count':0,'chunk_count':0,'total_raw_bytes':0,'total_character_count':0,'forms':list(FORMS),'per_company_stats':rows,'failed_documents':[],'request_count':0,'retry_count':0,'redirect_count':0,'rate_limit_count':0,'network_executed':False,'model_calls':0}
 op=Path(a.output); op.parent.mkdir(parents=True,exist_ok=True); tmp=op.with_suffix(op.suffix+'.tmp'); tmp.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); tmp.replace(op); print(json.dumps({'network_executed':False,'company_count':len(rows),'document_count':out['document_count']}))
if __name__=='__main__':
 try: main()
 except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
