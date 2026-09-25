import hashlib,json,re
from datetime import date,datetime,timezone
from pathlib import Path
from .sec_parser import clean_html,identify_sections
from .chunker import chunk_sections
_SYMBOL=re.compile(r'^[A-Z][A-Z0-9.\-]{0,9}$'); _CIK=re.compile(r'^\d{1,10}$'); _ACC=re.compile(r'^\d{10}-\d{2}-\d{6}$'); _FORMS={'10-K','10-K/A','10-Q','10-Q/A','8-K','8-K/A'}
def iso(v):
 if not isinstance(v,str): raise ValueError('invalid as_of')
 try: datetime.fromisoformat(v.replace('Z','+00:00')) if 'T' in v else date.fromisoformat(v)
 except ValueError: raise ValueError('invalid as_of')
def cik(v):
 if not isinstance(v,(str,int)) or not _CIK.fullmatch(str(v)) or int(v)==0: raise ValueError('invalid CIK')
 return str(v).zfill(10)
def build_sec_ingestion(raw_content, metadata, symbol, as_of, *, input_file='synthetic.html', input_sha256=None, target_chars=2000, overlap_chars=250):
 symbol=symbol.strip().upper(); iso(as_of)
 if not _SYMBOL.fullmatch(symbol): raise ValueError('invalid symbol')
 if not isinstance(metadata,dict): raise ValueError('metadata must be object')
 ms=str(metadata.get('symbol','')).strip().upper();
 if ms!=symbol: raise ValueError('symbol conflict')
 C=cik(metadata.get('cik')); acc=metadata.get('accession_number');
 if not isinstance(acc,str) or not _ACC.fullmatch(acc): raise ValueError('invalid accession')
 form=str(metadata.get('form','')).strip().upper()
 if form not in _FORMS: raise ValueError('invalid form')
 for k in ('accepted_at','published_at'):
  if metadata.get(k): iso(metadata[k]);
  if metadata.get(k) and str(metadata[k]).replace('Z','+00:00') > str(as_of).replace('Z','+00:00'): raise ValueError('filing after as_of')
 raw=raw_content if isinstance(raw_content,str) else raw_content.decode('utf-8'); digest=input_sha256 or hashlib.sha256(raw.encode()).hexdigest(); text=clean_html(raw); sections=identify_sections(text)
 docid=hashlib.sha256(f'{symbol}|{C}|{acc}|{form}|{digest}'.encode()).hexdigest()[:24]
 chunks=chunk_sections(sections,target_chars=target_chars,overlap_chars=overlap_chars)
 for i,ch in enumerate(chunks):
  ch.update(document_id=docid,symbol=symbol,cik=C,accession_number=acc,form=form,filing_date=metadata.get('filing_date'),accepted_at=metadata.get('accepted_at'),source_url=metadata.get('source_url'),citation=f'{symbol} | {form} | {acc} | {ch["section_title"]} | chunk {ch["chunk_index"]} | {metadata.get("source_url")}')
  ch['chunk_id']=hashlib.sha256(f'{docid}|{ch["section_id"]}|{ch["chunk_index"]}|{ch["text"]}'.encode()).hexdigest()[:24]
 doc={'schema_version':'1.0','document_id':docid,'symbol':symbol,'cik':C,'accession_number':acc,'form':form,'filing_date':metadata.get('filing_date'),'report_date':metadata.get('report_date'),'accepted_at':metadata.get('accepted_at'),'published_at':metadata.get('published_at'),'as_of':as_of,'source_url':metadata.get('source_url'),'input_file':input_file,'input_sha256':digest,'parser_version':'sec-parser-1','title':metadata.get('title') or form,'sections':sections,'warnings':[]}
 manifest={'schema_version':'1.0','document_id':docid,'symbol':symbol,'cik':C,'accession_number':acc,'form':form,'as_of':as_of,'input_file':input_file,'input_sha256':digest,'section_count':len(sections),'chunk_count':len(chunks),'warning_count':0,'target_chars':target_chars,'overlap_chars':overlap_chars,'parser_version':'sec-parser-1','chunker_version':'char-v1','network_executed':False,'model_calls':0}
 return doc,chunks,manifest
