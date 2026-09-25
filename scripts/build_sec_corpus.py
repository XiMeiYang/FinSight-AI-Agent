#!/usr/bin/env python3
"""SEC candidate inventory and explicitly confirmed corpus downloader."""
from __future__ import annotations
import argparse,hashlib,json,os,sys
from pathlib import Path
from urllib.parse import urlparse
from finsight_rag.catalog import SecurityCatalog
from finsight_rag.ingestion import parse_time,build_sec_ingestion
from finsight_sec import SECClient,SECConfig
TARGETS=('NVDA','AMD','INTC','AVGO','QCOM'); FORMS=('10-K','10-Q')
def root_path(): return Path('.local_data').resolve()
def safe_file(path,root):
 p=Path(path); p=p if p.is_absolute() else Path.cwd()/p; q=p.resolve()
 if p.is_symlink() or not p.is_file() or root not in q.parents: raise ValueError('unsafe path')
 return q
def safe_out(path,root):
 p=Path(path); q=p.resolve();
 if root not in q.parents and q!=root: raise ValueError('unsafe output path')
 return q
def filing_url(cik,acc,doc): return f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/{doc}'
def rows(payload,rec,cutoff):
 r=payload.get('filings',{}).get('recent',{}); n=len(r.get('form',[])); out=[]
 for i in range(n):
  form=str(r['form'][i] or '').strip().upper(); acc=r.get('accessionNumber',[None]*n)[i]; doc=r.get('primaryDocument',[None]*n)[i]
  if form not in FORMS or not isinstance(acc,str) or not doc: continue
  try: available=parse_time(r.get('acceptanceDateTime',[None]*n)[i] or r.get('filingDate',[None]*n)[i],date_only_end=True)
  except ValueError: continue
  if available>cutoff: continue
  out.append({'ticker':rec['ticker'],'cik':rec['cik'],'form':form,'filing_date':r.get('filingDate',[None]*n)[i],'report_date':r.get('reportDate',[None]*n)[i],'accepted_at':r.get('acceptanceDateTime',[None]*n)[i],'published_at':r.get('filingDate',[None]*n)[i],'accession_number':acc,'primary_document':doc,'source_url':filing_url(rec['cik'],acc,doc)})
 return out
def inventory(catalog,subdir,symbols,as_of,max10k,max10q):
 cutoff=parse_time(as_of,date_only_end=True); out=[]
 for ticker in symbols:
  try: rec=catalog.resolve(ticker)
  except Exception: out.append({'ticker':ticker,'status':'invalid_identity','selected':[]}); continue
  fs=list(Path(subdir).glob(f'*{rec["cik"]}*json')); stats={k:0 for k in ('available_10k','available_10q','selected_10k','selected_10q','duplicates','after_as_of','missing_primary_document','invalid_identity')}
  if not fs: out.append({'ticker':ticker,'cik':rec['cik'],'company_name':rec.get('company_name'),'status':'missing_submissions','stats':stats,'selected':[]}); continue
  allr=[]; seen=set()
  for f in fs:
   try: allr.extend(rows(json.loads(f.read_text()),rec,cutoff))
   except Exception: continue
  unique=[]
  for x in allr:
   if x['accession_number'] in seen: stats['duplicates']+=1; continue
   seen.add(x['accession_number']); unique.append(x)
  unique.sort(key=lambda x:(x['filing_date'] or '',x['accession_number']),reverse=True); stats['available_10k']=sum(x['form']=='10-K' for x in unique); stats['available_10q']=sum(x['form']=='10-Q' for x in unique); sel=[x for x in unique if x['form']=='10-K'][:max10k]+[x for x in unique if x['form']=='10-Q'][:max10q]; stats['selected_10k']=sum(x['form']=='10-K' for x in sel); stats['selected_10q']=sum(x['form']=='10-Q' for x in sel)
  out.append({'ticker':ticker,'cik':rec['cik'],'company_name':rec.get('company_name'),'status':'candidate_only','stats':stats,'selected':sel})
 return out
def refresh_metadata(catalog, subdir, symbols, client):
    root=root_path(); sub=Path(subdir); sub.mkdir(parents=True,exist_ok=True); result={'network_executed':False,'request_count':0,'retry_count':0,'failed_companies':[]}
    for ticker in symbols:
        try: rec=catalog.resolve(ticker)
        except Exception: continue
        existing=list(sub.glob(f'*{rec["cik"]}*json'))
        if existing: continue
        try:
            payload=client.submissions(rec['cik']); raw=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode('utf-8'); stamp=rec['cik']+'_submissions_refresh'; (sub/(stamp+'.json')).write_bytes(raw); (sub/(stamp+'.sha256')).write_text(hashlib.sha256(raw).hexdigest(),encoding='utf-8'); result['network_executed']=True
        except Exception as exc: result['failed_companies'].append({'ticker':ticker,'error':type(exc).__name__})
    result['request_count']=sum(x.get('attempt_count',0) for x in client.request_metadata); result['retry_count']=sum(x.get('retry_count',0) for x in client.request_metadata); return result
def validate_candidate(manifest,root=None,catalog=None):
 if not isinstance(manifest,dict) or not manifest.get('candidates') or not manifest.get('as_of'): raise ValueError('invalid candidate manifest')
 cutoff=parse_time(manifest['as_of'],date_only_end=True); total=0
 if catalog is not None: mapping={r['ticker']:r['cik'] for r in catalog._records}
 else: mapping={r.get('ticker'):str(r.get('cik')) for r in manifest.get('ticker_mapping',[])}
 for company in manifest['candidates']:
  company_count=0; k_count=q_count=0
  for row in company.get('selected',[]):
   if row.get('form') not in FORMS or row.get('ticker')!=company.get('ticker') or str(row.get('cik'))!=str(company.get('cik')): raise ValueError('candidate identity conflict')
   if mapping and mapping.get(row['ticker']) != str(row['cik']): raise ValueError('candidate CIK not proven by mapping')
   company_count+=1; total+=1; k_count += row['form']=='10-K'; q_count += row['form']=='10-Q'
   if total>100 or company_count>20 or k_count>5 or q_count>15: raise ValueError('candidate limits exceeded')
   try:
    if parse_time(row.get('accepted_at') or row.get('filing_date'),date_only_end=True)>cutoff: raise ValueError('candidate after as_of')
   except ValueError as exc:
    if str(exc)=='candidate after as_of': raise
   p=urlparse(row.get('source_url',''))
   if p.scheme!='https' or p.hostname!='www.sec.gov' or not p.path.startswith('/Archives/edgar/data/') or p.username or p.port not in (None,443): raise ValueError('unsafe SEC URL')
def download_corpus(manifest,outdir,user_agent,client=None):
 if not user_agent or '@' not in user_agent: raise ValueError('FINSIGHT_SEC_USER_AGENT is required')
 root=root_path(); out=safe_out(outdir,root); out.mkdir(parents=True,exist_ok=True); client=client or SECClient(SECConfig(user_agent=user_agent)); total=0; stats={'request_count':0,'retry_count':0,'redirect_count':0,'rate_limit_count':0,'timeout_count':0,'downloaded_bytes':0,'failed_documents':[]}; company=[]
 for co in manifest['candidates']:
  selected=co.get('selected',[]); croot=out/co['ticker']; rawd=croot/'raw'; metad=croot/'metadata'; docs=croot/'documents'; chunks=croot/'chunks'; mans=croot/'manifests'
  for d in (rawd,metad,docs,chunks,mans): d.mkdir(parents=True,exist_ok=True)
  done=0; sec=0; chk=0
  for row in selected:
   try:
    raw,digest=client.download_raw(row['source_url']);
    if len(raw)>50*1024*1024 or total+len(raw)>500*1024*1024: raise ValueError('download budget exceeded')
    total+=len(raw); stem=row['accession_number'].replace('-',''); rawp=rawd/(stem+'.bin'); rawp.write_bytes(raw); meta=dict(row,symbol=row['ticker'],retrieved_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),raw_sha256=digest,input_file=str(rawp.relative_to(root)))
    metap=metad/(stem+'.json'); metap.write_text(json.dumps(meta,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); doc,chs,man=build_sec_ingestion(raw,meta,row['ticker'],manifest['as_of'],input_file=str(rawp.relative_to(root)),input_sha256=digest); dp=docs/(doc['document_id']+'.json'); cp=chunks/(doc['document_id']+'.jsonl'); mp=mans/(doc['document_id']+'.json'); dp.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); cp.write_text('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in chs)+'\n',encoding='utf-8'); mp.write_text(json.dumps(man,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); done+=1; sec+=len(doc['sections']); chk+=len(chs)
   except Exception as exc: stats['failed_documents'].append({'ticker':row.get('ticker'),'accession_number':row.get('accession_number'),'error':type(exc).__name__})
  company.append({'ticker':co['ticker'],'document_count':done,'section_count':sec,'chunk_count':chk})
 stats['request_count']=sum(x.get('attempt_count',0) for x in client.request_metadata); stats['retry_count']=sum(x.get('retry_count',0) for x in client.request_metadata); stats['downloaded_bytes']=total; result={'corpus_id':'semiconductor-peer-corpus','as_of':manifest['as_of'],'symbols':[x['ticker'] for x in manifest['candidates']],'company_count':len(company),'document_count':sum(x['document_count'] for x in company),'section_count':sum(x['section_count'] for x in company),'chunk_count':sum(x['chunk_count'] for x in company),'total_raw_bytes':total,'per_company_stats':company,'failed_documents':stats['failed_documents'],'request_count':stats['request_count'],'retry_count':stats['retry_count'],'redirect_count':sum(1 for x in client.request_metadata if x.get('redirect_count',0)),'rate_limit_count':sum(1 for x in client.request_metadata if x.get('retry_reason')=='rate_limited'),'network_executed':bool(stats['request_count']),'model_calls':0}; out.joinpath('semiconductor-peer-corpus.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); return result
def main():
 p=argparse.ArgumentParser(); p.add_argument('--ticker-mapping'); p.add_argument('--submissions-dir'); p.add_argument('--candidate-manifest'); p.add_argument('--output'); p.add_argument('--output-dir'); p.add_argument('--as-of',default='2026-09-18T23:59:59Z'); p.add_argument('--symbols',default=','.join(TARGETS)); p.add_argument('--candidate-only',action='store_true'); p.add_argument('--network',action='store_true'); p.add_argument('--refresh-metadata',action='store_true'); p.add_argument('--max-10k',type=int,default=5); p.add_argument('--max-10q',type=int,default=15); a=p.parse_args(); root=root_path()
 if a.network and a.refresh_metadata:
  if not a.ticker_mapping or not a.submissions_dir or not a.output: raise SystemExit('ticker mapping, submissions dir and output are required')
  if not os.getenv('FINSIGHT_SEC_USER_AGENT'): raise SystemExit('FINSIGHT_SEC_USER_AGENT is required before network access')
  tm=safe_file(a.ticker_mapping,root); client=SECClient(SECConfig(user_agent=os.getenv('FINSIGHT_SEC_USER_AGENT'))); refresh=refresh_metadata(SecurityCatalog.from_json(tm),a.submissions_dir,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],client); rowsx=inventory(SecurityCatalog.from_json(tm),a.submissions_dir,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],a.as_of,a.max_10k,a.max_10q); out={'schema_version':'1.0','as_of':a.as_of,'ticker_mapping':[{k:v for k,v in r.items() if k in ('ticker','cik','company_name')} for r in SecurityCatalog.from_json(tm)._records if r['ticker'] in [x.strip().upper() for x in a.symbols.split(',')]],'candidates':rowsx,'network_executed':refresh['network_executed'],'model_calls':0,'refresh':refresh}; op=safe_out(a.output,root); op.parent.mkdir(parents=True,exist_ok=True); op.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); print(json.dumps({'network_executed':refresh['network_executed'],'refresh':refresh})); return
 if a.network:
  if not a.candidate_manifest: raise SystemExit('--candidate-manifest is required with --network')
  if not os.getenv('FINSIGHT_SEC_USER_AGENT'): raise SystemExit('FINSIGHT_SEC_USER_AGENT is required before network access')
  cm=safe_file(a.candidate_manifest,root); manifest=json.loads(cm.read_text()); catalog=None
  validate_candidate(manifest,root,catalog); print(json.dumps(download_corpus(manifest,a.output_dir,os.getenv('FINSIGHT_SEC_USER_AGENT')),ensure_ascii=False)); return
 if not a.ticker_mapping or not a.submissions_dir or not a.output: raise SystemExit('ticker mapping, submissions dir and output are required')
 tm=safe_file(a.ticker_mapping,root); sub=Path(a.submissions_dir).resolve();
 if root not in sub.parents: raise SystemExit('unsafe submissions directory')
 rowsx=inventory(SecurityCatalog.from_json(tm),sub,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],a.as_of,a.max_10k,a.max_10q); out={'schema_version':'1.0','as_of':a.as_of,'ticker_mapping':[{k:v for k,v in r.items() if k in ('ticker','cik','company_name')} for r in SecurityCatalog.from_json(tm)._records if r['ticker'] in [x.strip().upper() for x in a.symbols.split(',')]],'candidates':rowsx,'network_executed':False,'model_calls':0}; op=safe_out(a.output,root); op.parent.mkdir(parents=True,exist_ok=True); tmp=op.with_suffix(op.suffix+'.tmp'); tmp.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); tmp.replace(op); print(json.dumps({'network_executed':False,'company_count':len(rowsx),'document_count':sum(len(x.get('selected',[])) for x in rowsx)}))
if __name__=='__main__':
 try: main()
 except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
