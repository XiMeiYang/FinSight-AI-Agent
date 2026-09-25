"""Offline security catalog and RAG coverage lookup."""
from __future__ import annotations
import json,re
from pathlib import Path

def normalize_ticker(value):
    value=str(value or '').strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,9}',value): raise ValueError('invalid ticker')
    return value

def normalize_cik(value):
    text=str(value or '').strip()
    if not re.fullmatch(r'\d{1,10}',text) or int(text)==0: raise ValueError('invalid CIK')
    return text.zfill(10)

class SecurityCatalog:
    def __init__(self, records):
        self._records=tuple(sorted(records,key=lambda r:(r['ticker'],r.get('company_name') or '',r['cik'])))
    @classmethod
    def from_json(cls,path):
        payload=json.loads(Path(path).read_text(encoding='utf-8'))
        rows=payload.values() if isinstance(payload,dict) and not {'ticker','cik_str'} <= set(payload) else [payload]
        records=[]
        for row in rows:
            ticker=normalize_ticker(row.get('ticker')); cik=normalize_cik(row.get('cik_str',row.get('cik')))
            records.append({'ticker':ticker,'company_name':row.get('title') or row.get('company_name'),'cik':cik,'exchange':row.get('exchange')})
        return cls(records)
    def resolve(self,ticker):
        t=normalize_ticker(ticker); matches=[r for r in self._records if r['ticker']==t]
        if len(matches)!=1: raise KeyError('ticker not found or ambiguous')
        return dict(matches[0])
    def search(self,query,limit=20):
        q=str(query or '').strip().lower()
        rows=[r for r in self._records if r['ticker'].lower().startswith(q) or q in str(r.get('company_name') or '').lower()]
        return [dict(r) for r in rows[:max(0,int(limit))]]
