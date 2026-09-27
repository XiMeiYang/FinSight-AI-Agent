#!/usr/bin/env python3
"""SEC candidate inventory and explicitly confirmed corpus downloader."""
from __future__ import annotations
import argparse,hashlib,json,os,sys,tempfile,shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from finsight_rag.catalog import SecurityCatalog
from finsight_rag.ingestion import parse_time,build_sec_ingestion
from finsight_sec import SECClient,SECConfig
TARGETS=('NVDA','AMD','INTC','AVGO','QCOM'); FORMS=('10-K','10-Q')
SEC_DEFAULT_MAX_RETRIES=2; MAX_DOCUMENT_BYTES=50*1024*1024; MAX_TOTAL_BYTES=500*1024*1024
def root_path(): return Path('.local_data').resolve()
def safe_file(path,root):
 p=Path(path); p=p if p.is_absolute() else Path.cwd()/p; q=p.resolve()
 if p.is_symlink() or not p.is_file() or root not in q.parents: raise ValueError('unsafe path')
 return q
def safe_out(path,root):
 p=Path(path)
 if any(part.is_symlink() for part in [p,*p.parents]): raise ValueError('unsafe output path')
 q=p.resolve();
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
 seen_accessions=set()
 for company in manifest['candidates']:
  company_count=0; k_count=q_count=0
  for row in company.get('selected',[]):
   if not isinstance(company.get('ticker'),str) or not company['ticker'].isupper() or not company['ticker'].isalnum(): raise ValueError('invalid ticker')
   if row.get('form') not in FORMS or row.get('ticker')!=company.get('ticker') or str(row.get('cik'))!=str(company.get('cik')): raise ValueError('candidate identity conflict')
   if not str(row.get('cik','')).isdigit() or len(str(row.get('cik'))) != 10: raise ValueError('invalid CIK')
   acc=row.get('accession_number','')
   if not isinstance(acc,str) or not __import__('re').fullmatch(r'\d{10}-\d{2}-\d{6}',acc): raise ValueError('invalid accession')
   if acc in seen_accessions: raise ValueError('duplicate accession')
   seen_accessions.add(acc)
   doc=row.get('primary_document','')
   if not isinstance(doc,str) or Path(doc).name!=doc or doc in ('','.','..') or '/' in doc or '\\' in doc: raise ValueError('unsafe primary document')
   if mapping and mapping.get(row['ticker']) != str(row['cik']): raise ValueError('candidate CIK not proven by mapping')
   company_count+=1; total+=1; k_count += row['form']=='10-K'; q_count += row['form']=='10-Q'
   if total>100 or company_count>20 or k_count>5 or q_count>15: raise ValueError('candidate limits exceeded')
   try:
    if parse_time(row.get('accepted_at') or row.get('filing_date'),date_only_end=True)>cutoff: raise ValueError('candidate after as_of')
   except ValueError as exc: raise ValueError('invalid candidate time') from exc
   p=urlparse(row.get('source_url',''))
   expected=f"/Archives/edgar/data/{int(row['cik'])}/{acc.replace('-', '')}/{doc}"
   if p.scheme!='https' or p.hostname!='www.sec.gov' or p.path!=expected or p.username or p.port not in (None,443): raise ValueError('unsafe SEC URL')
def _ordered_documents(manifest, latest=False, max_documents=None, max_per_company=None):
 """Stable, bounded selection; this function performs no I/O."""
 rows=[]
 for co in sorted(manifest.get('candidates',[]), key=lambda x:x.get('ticker','')):
  selected=list(co.get('selected',[]))
  selected.sort(key=lambda x:(x.get('ticker',''),x.get('form',''),x.get('accepted_at') or x.get('filing_date') or '',x.get('accession_number','')), reverse=False)
  if latest:
   selected=[max((r for r in selected if r.get('form')==form), key=lambda x:(x.get('accepted_at') or x.get('filing_date') or '',x.get('accession_number','')), default=None) for form in FORMS]
   selected=[r for r in selected if r]
  if max_per_company is not None: selected=selected[:max_per_company]
  rows.extend(selected)
 if max_documents is not None: rows=rows[:max_documents]
 return rows

def _products_complete(croot, row, digest=None):
 stem=row['accession_number'].replace('-','')
 bundle=croot if croot.name.startswith('.batch-') else croot/'filings'/stem
 paths=[bundle/'raw.bin',bundle/'metadata.json']; meta=paths[1]
 try:
  if not all(p.is_file() and not p.is_symlink() for p in paths): return False
  actual=hashlib.sha256(paths[0].read_bytes()).hexdigest()
  if digest is not None and actual!=digest: return False
  obj=json.loads(meta.read_text());
  if obj.get('accession_number')!=row.get('accession_number') or obj.get('ticker')!=row.get('ticker') or str(obj.get('cik'))!=str(row.get('cik')) or obj.get('raw_sha256')!=actual: return False
  doc_id=obj.get('document_id')
  if not doc_id: return False
  files=[bundle/'document.json',bundle/'chunks.jsonl',bundle/'ingestion-manifest.json']
  if not all(p.is_file() and not p.is_symlink() for p in files): return False
  doc=json.loads(files[0].read_text()); ing=json.loads(files[2].read_text())
  chunks=files[1].read_text().splitlines(); parsed=[json.loads(x) for x in chunks]
  if not parsed: return False
  meta_bytes=meta.read_bytes(); doc_bytes=files[0].read_bytes(); chunk_bytes=files[1].read_bytes()
  expected={'raw_sha256':actual,'metadata_sha256':hashlib.sha256(meta_bytes).hexdigest(),'document_sha256':hashlib.sha256(doc_bytes).hexdigest(),'chunks_sha256':hashlib.sha256(chunk_bytes).hexdigest()}
  if any(ing.get(k)!=v for k,v in expected.items()): return False
  identity={'document_id':doc_id,'symbol':row.get('ticker'),'cik':str(row.get('cik')),'accession_number':row.get('accession_number'),'form':row.get('form')}
  return (all(doc.get(k)==v for k,v in identity.items()) and all(ing.get(k)==v for k,v in identity.items()) and all(all(x.get(k)==v for k,v in identity.items()) for x in parsed))
 except Exception: return False

def _has_related(croot, row):
 stem=row['accession_number'].replace('-','')
 bundle=croot/'filings'/stem
 if bundle.exists() or bundle.is_symlink(): return True
 for d in ('raw','metadata','documents','chunks','manifests'):
  p=croot/d
  if not p.exists(): continue
  for f in p.iterdir():
   if stem in f.name: return True
   if f.suffix=='.json':
    try:
     if json.loads(f.read_text()).get('accession_number')==row['accession_number']: return True
    except Exception: pass
   if f.suffix=='.jsonl':
    try:
     if any(json.loads(line).get('accession_number')==row['accession_number'] for line in f.read_text().splitlines() if line.strip()): return True
    except Exception: pass
 return False

def _validate_output_tree(out, planned):
 """Reject pre-existing symlink nodes before any network request."""
 for row in planned:
  croot = out / str(row.get('ticker', ''))
  if croot.is_symlink():
   raise ValueError('unsafe output path')
  for name in ('filings',):
   node = croot / name
   if node.is_symlink():
    raise ValueError('unsafe output path')

def _write_json(path, obj):
 path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); json.loads(path.read_text(encoding='utf-8'))

def download_corpus(manifest,outdir,user_agent,client=None,*,dry_run=False,max_documents=None,max_documents_per_company=None,latest_per_form_per_company=False,overwrite=False):
 validate_candidate(manifest)
 if not dry_run and not user_agent: raise ValueError('FINSIGHT_SEC_USER_AGENT is required')
 if any(x is not None and x < 0 for x in (max_documents,max_documents_per_company)): raise ValueError('invalid document budget')
 planned=_ordered_documents(manifest,latest_per_form_per_company,max_documents,max_documents_per_company)
 counts={co['ticker']:sum(r.get('ticker')==co['ticker'] for r in planned) for co in manifest['candidates']}
 result={'planned_document_count':len(planned),'planned_documents':[{'ticker':r.get('ticker'),'form':r.get('form'),'accession_number':r.get('accession_number')} for r in planned],'company_count':len(counts),'planned_10k_count':sum(r.get('form')=='10-K' for r in planned),'planned_10q_count':sum(r.get('form')=='10-Q' for r in planned),'attempted_document_count':0,'completed_document_count':0,'already_completed_count':0,'overwritten_document_count':0,'failed_document_count':0,'request_count':0,'retry_count':0,'downloaded_bytes':0,'network_executed':False,'model_calls':0,'per_company_counts':counts,'max_request_budget':len(planned)*(SEC_DEFAULT_MAX_RETRIES+1),'max_byte_budget':MAX_TOTAL_BYTES,'max_document_bytes':MAX_DOCUMENT_BYTES,'failed_documents':[]}
 if dry_run: result['status']='dry_run'; return result
 root=root_path(); out=safe_out(outdir,root); out.mkdir(parents=True,exist_ok=True); client=client or SECClient(SECConfig(user_agent=user_agent)); result['max_request_budget']=len(planned)*(getattr(getattr(client,'config',None),'max_retries',SEC_DEFAULT_MAX_RETRIES)+1); total=0
 _validate_output_tree(out, planned)
 for row in planned:
  result['attempted_document_count']+=1; croot=out/row['ticker']; filings=croot/'filings'; stem=row['accession_number'].replace('-',''); final=filings/stem
  try:
   filings.mkdir(parents=True,exist_ok=True)
   if filings.is_symlink() or final.is_symlink(): raise ValueError('unsafe output path')
   backup=filings/('.backup-'+stem)
   if backup.exists() and not final.exists(): os.replace(backup,final)
   elif backup.exists() and final.exists(): shutil.rmtree(backup)
   if _has_related(croot,row) and not overwrite:
    if _products_complete(croot,row): result['already_completed_count']+=1; continue
    raise ValueError('existing filing incomplete or identity/hash conflict')
   raw,reported_digest=client.download_raw(row['source_url']); digest=hashlib.sha256(raw).hexdigest(); result['downloaded_bytes']+=len(raw); result['network_executed']=True
   if reported_digest != digest: raise ValueError('raw digest mismatch')
   if len(raw)>MAX_DOCUMENT_BYTES or total+len(raw)>MAX_TOTAL_BYTES: raise ValueError('download budget exceeded')
   with tempfile.TemporaryDirectory(prefix='.batch-',dir=str(filings)) as td:
    t=Path(td); meta=dict(row,symbol=row['ticker'],raw_sha256=digest,retrieved_at=datetime.now(timezone.utc).isoformat(),input_file=f".local_data/rag/corpus/{row['ticker']}/filings/{stem}/raw.bin")
    _write_json(t/'metadata.json',meta)
    doc,chs,ing=build_sec_ingestion(raw,meta,row['ticker'],manifest['as_of'],input_file=meta['input_file'],input_sha256=digest)
    meta['document_id']=doc['document_id']; _write_json(t/'metadata.json',meta)
    ing['raw_sha256']=digest; ing['metadata_sha256']=hashlib.sha256((t/'metadata.json').read_bytes()).hexdigest(); ing['document_sha256']=hashlib.sha256(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2).encode()).hexdigest(); ing['chunks_sha256']=hashlib.sha256((''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in chs)).encode()).hexdigest()
    (t/'raw.bin').write_bytes(raw); _write_json(t/'document.json',doc); (t/'chunks.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in chs),encoding='utf-8'); [json.loads(x) for x in (t/'chunks.jsonl').read_text().splitlines()]; _write_json(t/'ingestion-manifest.json',ing)
    if not _products_complete(t, row): raise ValueError('bundle validation failed')
    # Commit the five-file batch with rollback. Existing files are moved into
    # the same temporary directory first; a failed replacement restores the
    # prior set and removes any newly committed members.
    backups=[]
    try:
     backup=filings/('.backup-'+stem)
     if backup.exists() and not final.exists(): os.replace(backup,final)
     elif backup.exists() and final.exists(): shutil.rmtree(backup)
     if final.exists() and not overwrite: raise ValueError('existing filing incomplete or identity/hash conflict')
     if final.exists(): os.replace(final,backup); backups.append((backup,final))
     os.replace(t,final)
    except Exception:
     for backup,dst in reversed(backups):
      if backup.exists() and not dst.exists(): os.replace(backup,dst)
     raise
   total+=len(raw); result['completed_document_count']+=1; result['overwritten_document_count']+=int(overwrite and bool(backups))
  except Exception as exc:
   result['failed_document_count']+=1; result['failed_documents'].append({'ticker':row.get('ticker'),'accession_number':row.get('accession_number'),'error':type(exc).__name__}); break
 result['request_count']=sum(x.get('attempts_total',x.get('attempt_count',0)) for x in getattr(client,'request_metadata',[])); result['retry_count']=sum(x.get('retry_count',0) for x in getattr(client,'request_metadata',[])); result['document_count']=result['completed_document_count']; result['status']='failed' if result['failed_document_count'] and not result['completed_document_count'] else ('partial' if result['failed_document_count'] else ('completed' if result['completed_document_count']+result['already_completed_count']==result['planned_document_count'] else 'planned')); return result
def main():
 p=argparse.ArgumentParser(); p.add_argument('--ticker-mapping'); p.add_argument('--submissions-dir'); p.add_argument('--candidate-manifest'); p.add_argument('--output'); p.add_argument('--output-dir'); p.add_argument('--as-of',default='2026-09-18T23:59:59Z'); p.add_argument('--symbols',default=','.join(TARGETS)); p.add_argument('--candidate-only',action='store_true'); p.add_argument('--network',action='store_true'); p.add_argument('--refresh-metadata',action='store_true'); p.add_argument('--dry-run',action='store_true'); p.add_argument('--max-documents',type=int); p.add_argument('--max-documents-per-company',type=int); p.add_argument('--latest-per-form-per-company',action='store_true'); p.add_argument('--overwrite',action='store_true'); p.add_argument('--max-10k',type=int,default=5); p.add_argument('--max-10q',type=int,default=15); a=p.parse_args(); root=root_path()
 if a.network and a.refresh_metadata:
  if not a.ticker_mapping or not a.submissions_dir or not a.output: raise SystemExit('ticker mapping, submissions dir and output are required')
  if not os.getenv('FINSIGHT_SEC_USER_AGENT'): raise SystemExit('FINSIGHT_SEC_USER_AGENT is required before network access')
  tm=safe_file(a.ticker_mapping,root); client=SECClient(SECConfig(user_agent=os.getenv('FINSIGHT_SEC_USER_AGENT'))); refresh=refresh_metadata(SecurityCatalog.from_json(tm),a.submissions_dir,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],client); rowsx=inventory(SecurityCatalog.from_json(tm),a.submissions_dir,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],a.as_of,a.max_10k,a.max_10q); out={'schema_version':'1.0','as_of':a.as_of,'ticker_mapping':[{k:v for k,v in r.items() if k in ('ticker','cik','company_name')} for r in SecurityCatalog.from_json(tm)._records if r['ticker'] in [x.strip().upper() for x in a.symbols.split(',')]],'candidates':rowsx,'network_executed':refresh['network_executed'],'model_calls':0,'refresh':refresh}; op=safe_out(a.output,root); op.parent.mkdir(parents=True,exist_ok=True); op.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); print(json.dumps({'network_executed':refresh['network_executed'],'refresh':refresh})); return
 if a.network or a.dry_run:
  if not a.candidate_manifest: raise SystemExit('--candidate-manifest is required with --network')
  if a.network and not os.getenv('FINSIGHT_SEC_USER_AGENT'): raise SystemExit('FINSIGHT_SEC_USER_AGENT is required before network access')
  cm=safe_file(a.candidate_manifest,root); manifest=json.loads(cm.read_text()); catalog=None
  validate_candidate(manifest,root,catalog); print(json.dumps(download_corpus(manifest,a.output_dir or '.local_data/rag/corpus',os.getenv('FINSIGHT_SEC_USER_AGENT') if a.network else '',dry_run=a.dry_run,max_documents=a.max_documents,max_documents_per_company=a.max_documents_per_company,latest_per_form_per_company=a.latest_per_form_per_company,overwrite=a.overwrite),ensure_ascii=False)); return
 if not a.ticker_mapping or not a.submissions_dir or not a.output: raise SystemExit('ticker mapping, submissions dir and output are required')
 tm=safe_file(a.ticker_mapping,root); sub=Path(a.submissions_dir).resolve();
 if root not in sub.parents: raise SystemExit('unsafe submissions directory')
 rowsx=inventory(SecurityCatalog.from_json(tm),sub,[x.strip().upper() for x in a.symbols.split(',') if x.strip()],a.as_of,a.max_10k,a.max_10q); out={'schema_version':'1.0','as_of':a.as_of,'ticker_mapping':[{k:v for k,v in r.items() if k in ('ticker','cik','company_name')} for r in SecurityCatalog.from_json(tm)._records if r['ticker'] in [x.strip().upper() for x in a.symbols.split(',')]],'candidates':rowsx,'network_executed':False,'model_calls':0}; op=safe_out(a.output,root); op.parent.mkdir(parents=True,exist_ok=True); tmp=op.with_suffix(op.suffix+'.tmp'); tmp.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8'); tmp.replace(op); print(json.dumps({'network_executed':False,'company_count':len(rowsx),'document_count':sum(len(x.get('selected',[])) for x in rowsx)}))
if __name__=='__main__':
 try: main()
 except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
