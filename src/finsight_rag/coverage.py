"""Coverage is separate from security identity."""
from __future__ import annotations
from typing import TypedDict
class CoverageRecord(TypedDict):
    ticker: str
    cik: str
    status: str
    filing_count: int
    chunk_count: int
    reason: str

def rag_coverage(catalog_record, corpus_records):
    ticker=catalog_record['ticker']; cik=catalog_record['cik']; rows=[r for r in corpus_records if r.get('ticker')==ticker and r.get('cik')==cik]
    if not rows: return {'ticker':ticker,'cik':cik,'status':'not_built','filing_count':0,'chunk_count':0,'reason':'no corpus manifest'}
    status=rows[0].get('status','available'); return {'ticker':ticker,'cik':cik,'status':status,'filing_count':sum(int(r.get('filing_count',0)) for r in rows),'chunk_count':sum(int(r.get('chunk_count',0)) for r in rows),'reason':rows[0].get('reason','')}
