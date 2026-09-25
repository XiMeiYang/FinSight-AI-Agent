#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from finsight_research import build_research_snapshot
from finsight_research.local_loader import load_json,atomic_write_json
ROOT=Path(__file__).resolve().parents[1]; FIXTURE=ROOT/'tests/fixtures'; DATA_ROOT=ROOT/'.local_data'
def fixture(a):
 if a.symbol.strip().upper()!='TEST': raise ValueError('fixture mode only accepts TEST')
 m=json.loads((FIXTURE/'alpha_vantage_daily.synthetic.json').read_text()); f=json.loads((FIXTURE/'sec_companyfacts.synthetic.json').read_text()); s=json.loads((FIXTURE/'sec_submissions.synthetic.json').read_text())
 rows=[{'symbol':'TEST','as_of':d,'timestamp':d+'T00:00:00Z','open':float(v['1. open']),'high':float(v['2. high']),'low':float(v['3. low']),'close':float(v['4. close']),'volume':int(v['5. volume']),'adjusted_close':None,'currency':None,'source':'alpha_vantage','source_url':'https://www.alphavantage.co/query','retrieved_at':'2024-01-04T00:00:00Z'} for d,v in m['Time Series (Daily)'].items()]
 return build_research_snapshot(symbol='TEST',market_data={'source':'alpha_vantage','source_url':'https://www.alphavantage.co/query','rows':rows},company_facts=f,filings=s,as_of=a.as_of,data_mode='synthetic',snapshot_id='snapshot-fixture',run_id='run-fixture',clock=lambda:'2024-01-04T00:00:00Z')
def saved(a):
 requested = a.symbol.strip().upper()
 vals=[a.market_normalized,a.market_raw,a.sec_companyfacts_normalized,a.sec_companyfacts_raw,a.sec_submissions_normalized,a.sec_submissions_raw,a.ticker_mapping_normalized,a.ticker_mapping_raw]
 if any(not x for x in vals): raise ValueError('saved_snapshot requires all explicit input files')
 market,mn=load_json(a.market_normalized,data_root=DATA_ROOT); _,mr=load_json(a.market_raw,data_root=DATA_ROOT); facts,fn=load_json(a.sec_companyfacts_normalized,data_root=DATA_ROOT); _,fr=load_json(a.sec_companyfacts_raw,data_root=DATA_ROOT); filings,sn=load_json(a.sec_submissions_normalized,data_root=DATA_ROOT); _,sr=load_json(a.sec_submissions_raw,data_root=DATA_ROOT); mapping,mn_t=load_json(a.ticker_mapping_normalized,data_root=DATA_ROOT); _,mr_t=load_json(a.ticker_mapping_raw,data_root=DATA_ROOT)
 for normalized, raw in ((mn, mr), (fn, fr), (sn, sr), (mn_t, mr_t)):
  if Path(normalized['input_file']).stem != Path(raw['input_file']).stem: raise ValueError('raw and normalized input files do not correspond')
 if facts.get('raw_sha256') and facts['raw_sha256']!=fr['sha256']: raise ValueError('Company Facts raw SHA-256 mismatch')
 entries = list(mapping.values()) if isinstance(mapping, dict) and not (mapping.get('ticker') or mapping.get('symbol')) else [mapping]
 matches = [e for e in entries if isinstance(e, dict) and str(e.get('ticker','')).strip().upper() == requested]
 if len(matches) != 1: raise ValueError('ticker mapping must contain exactly one requested ticker')
 mapping = matches[0]
 mapped_ticker=str(mapping.get('ticker',mapping.get('symbol',''))).strip().upper(); mapped_cik=str(mapping.get('cik',mapping.get('cik_str',''))).zfill(10)
 if requested != mapped_ticker or market.get('symbol','').strip().upper()!=mapped_ticker or str(facts.get('cik')).zfill(10)!=mapped_cik or str(filings.get('cik')).zfill(10)!=mapped_cik: raise ValueError('saved input identity mismatch')
 submissions_url=f'https://data.sec.gov/submissions/CIK{mapped_cik}.json'
 market=dict(market,raw_sha256=mr['sha256'],normalized_sha256=mn['sha256'],input_file=mn['input_file']); facts=dict(facts,normalized_sha256=fn['sha256'],input_file=fn['input_file']); filings=dict(filings,normalized_sha256=sn['sha256'],raw_sha256=sr['sha256'],input_file=sn['input_file'],source_url=submissions_url)
 snap=build_research_snapshot(symbol=mapped_ticker,market_data=market,company_facts=facts,filings=filings,ticker_mapping=dict(mapping,raw_sha256=mr_t['sha256'],normalized_sha256=mn_t['sha256'],input_file=mn_t['input_file']),as_of=a.as_of,data_mode='saved_snapshot')
 snap['sources']=[
 {'source_id':'market-alpha-vantage','source_type':'market','provider':'alpha_vantage','source_url':market.get('source_url'),'retrieved_at':market.get('retrieved_at'),'data_as_of':snap['market_data'].get('data_as_of'),'published_at':None,'raw_sha256':mr['sha256'],'normalized_sha256':mn['sha256'],'input_file':mn['input_file']},
 {'source_id':'sec-companyfacts','source_type':'sec_companyfacts','provider':'sec_edgar','source_url':facts.get('source_url'),'retrieved_at':facts.get('retrieved_at'),'data_as_of':None,'published_at':None,'raw_sha256':fr['sha256'],'normalized_sha256':fn['sha256'],'input_file':fn['input_file']},
 {'source_id':'sec-submissions','source_type':'sec_submissions','provider':'sec_edgar','source_url':filings.get('source_url'),'retrieved_at':filings.get('retrieved_at'),'data_as_of':None,'published_at':None,'raw_sha256':sr['sha256'],'normalized_sha256':sn['sha256'],'input_file':sn['input_file']},
 {'source_id':'sec-ticker-mapping','source_type':'sec_ticker_mapping','provider':'sec_edgar','source_url':mapping.get('source_url','https://www.sec.gov/files/company_tickers.json'),'retrieved_at':mapping.get('retrieved_at'),'data_as_of':None,'published_at':None,'raw_sha256':mr_t['sha256'],'normalized_sha256':mn_t['sha256'],'input_file':mn_t['input_file']},
 ]
 snap['run_record'].update(selected_files=[mn['input_file'],mr['input_file'],fn['input_file'],fr['input_file'],sn['input_file'],sr['input_file'],mn_t['input_file'],mr_t['input_file']],file_hash_verification='passed',identity_verification='passed',point_in_time_filter={'as_of':snap['as_of'],'filtered_count':snap['data_quality']['point_in_time_filtered_count']},snapshot_write='pending')
 return snap
def main():
 p=argparse.ArgumentParser(); p.add_argument('symbol'); p.add_argument('--fixture',action='store_true'); p.add_argument('--saved-snapshot',action='store_true'); p.add_argument('--as-of',required=True); p.add_argument('--output'); p.add_argument('--overwrite',action='store_true')
 for n in ('market-normalized','market-raw','sec-companyfacts-normalized','sec-companyfacts-raw','sec-submissions-normalized','sec-submissions-raw','ticker-mapping-normalized','ticker-mapping-raw'): p.add_argument('--'+n,dest=n.replace('-','_'))
 a=p.parse_args()
 if a.fixture==a.saved_snapshot: p.error('choose exactly one of --fixture or --saved-snapshot')
 out=fixture(a) if a.fixture else saved(a)
 if a.output:
  out['run_record']['snapshot_write']='completed'
  print(atomic_write_json(a.output,out,data_root=DATA_ROOT,overwrite=a.overwrite)[0])
 else: print(json.dumps(out,ensure_ascii=False,indent=2)+'\n',end='')
if __name__=='__main__':
 try: main()
 except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
