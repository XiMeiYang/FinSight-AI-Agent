"""Offline SEC filing ingestion with strict deterministic contracts."""
from __future__ import annotations
import hashlib,re
from datetime import date,datetime,time,timezone
from urllib.parse import urlparse
from .chunker import chunk_sections
from .sec_parser import clean_html,identify_sections
_SYMBOL=re.compile(r'^[A-Z][A-Z0-9.\-]{0,9}$'); _CIK=re.compile(r'^\d{1,10}$'); _ACC=re.compile(r'^\d{10}-\d{2}-\d{6}$'); _FORMS={'10-K','10-K/A','10-Q','10-Q/A','8-K','8-K/A'}; _SEC_HOSTS={'www.sec.gov','data.sec.gov'}
def parse_time(value, *, date_only_end=False):
    if not isinstance(value,str) or not value.strip(): raise ValueError('invalid time')
    text=value.strip()
    if re.fullmatch(r'\d{14}',text):
        from zoneinfo import ZoneInfo
        return datetime.strptime(text,'%Y%m%d%H%M%S').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',text):
            return datetime.combine(date.fromisoformat(text),time.max if date_only_end else time.min,timezone.utc)
        parsed=datetime.fromisoformat(text.replace('Z','+00:00'))
        if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError,ValueError): raise ValueError('invalid time')
def iso(value): parse_time(value)
def cik(value):
    if not isinstance(value,(str,int)) or not _CIK.fullmatch(str(value).strip()) or int(value)==0: raise ValueError('invalid CIK')
    return str(value).strip().zfill(10)
def _source_url(value):
    if not isinstance(value,str) or not value: raise ValueError('missing source_url')
    p=urlparse(value)
    if p.scheme!='https' or p.username or p.password or p.hostname not in _SEC_HOSTS or p.port not in (None,443): raise ValueError('invalid source_url')
    return value
def build_sec_ingestion(raw_content,metadata,symbol,as_of,*,input_file='synthetic.html',input_sha256=None,target_chars=2000,overlap_chars=250):
    symbol=str(symbol).strip().upper()
    if not _SYMBOL.fullmatch(symbol): raise ValueError('invalid symbol')
    cutoff=parse_time(as_of,date_only_end=True)
    if not isinstance(metadata,dict): raise ValueError('metadata must be object')
    if str(metadata.get('symbol','')).strip().upper()!=symbol: raise ValueError('symbol conflict')
    company_cik=cik(metadata.get('cik')); accession=metadata.get('accession_number')
    if not isinstance(accession,str) or not _ACC.fullmatch(accession): raise ValueError('invalid accession')
    form=str(metadata.get('form','')).strip().upper()
    if form not in _FORMS: raise ValueError('invalid form')
    source_url=_source_url(metadata.get('source_url'))
    for key in ('filing_date','report_date'):
        if metadata.get(key) is not None: parse_time(metadata[key])
    for key in ('accepted_at','published_at'):
        if metadata.get(key) is not None and parse_time(metadata[key])>cutoff: raise ValueError('filing after as_of')
    if not isinstance(raw_content,(str,bytes)): raise ValueError('raw content must be text or bytes')
    raw_bytes=raw_content if isinstance(raw_content,bytes) else raw_content.encode('utf-8'); digest=hashlib.sha256(raw_bytes).hexdigest()
    if input_sha256 is not None and input_sha256!=digest: raise ValueError('input_sha256 mismatch')
    raw=raw_bytes.decode('utf-8'); text=clean_html(raw)
    if not text.strip(): raise ValueError('empty filing content')
    if not isinstance(target_chars,int) or target_chars<=0 or not isinstance(overlap_chars,int) or overlap_chars<0 or overlap_chars>=target_chars: raise ValueError('invalid chunk settings')
    sections=identify_sections(text); chunks=chunk_sections(sections,target_chars=target_chars,overlap_chars=overlap_chars)
    docid=hashlib.sha256(f'{symbol}|{company_cik}|{accession}|{form}|{digest}'.encode()).hexdigest()[:24]
    for item in chunks:
        item.update(document_id=docid,symbol=symbol,cik=company_cik,accession_number=accession,form=form,filing_date=metadata.get('filing_date'),accepted_at=metadata.get('accepted_at'),source_url=source_url,citation=f'{symbol} | {form} | {accession} | {item["section_title"]} | chunk {item["chunk_index"]} | {source_url}')
        item['chunk_id']=hashlib.sha256(f'{docid}|{item["section_id"]}|{item["chunk_index"]}|{item["text"]}'.encode()).hexdigest()[:24]
    document={'schema_version':'1.0','document_id':docid,'symbol':symbol,'cik':company_cik,'accession_number':accession,'form':form,'filing_date':metadata.get('filing_date'),'report_date':metadata.get('report_date'),'accepted_at':metadata.get('accepted_at'),'published_at':metadata.get('published_at'),'as_of':as_of,'source_url':source_url,'input_file':input_file,'input_sha256':digest,'parser_version':'sec-parser-1','title':metadata.get('title') or form,'sections':sections,'warnings':[]}
    manifest={'schema_version':'1.0','document_id':docid,'symbol':symbol,'cik':company_cik,'accession_number':accession,'form':form,'as_of':as_of,'input_file':input_file,'input_sha256':digest,'section_count':len(sections),'chunk_count':len(chunks),'warning_count':0,'target_chars':target_chars,'overlap_chars':overlap_chars,'parser_version':'sec-parser-1','chunker_version':'char-v1','network_executed':False,'model_calls':0}
    return document,chunks,manifest
