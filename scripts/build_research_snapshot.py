#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
from finsight_research import build_research_snapshot

def main():
    p=argparse.ArgumentParser(); p.add_argument("symbol"); p.add_argument("--fixture",action="store_true"); p.add_argument("--as-of",required=True); p.add_argument("--output")
    args=p.parse_args()
    if not args.fixture: p.error("only --fixture offline mode is available")
    if args.symbol.strip().upper() != "TEST": p.error("fixture mode only accepts TEST; it cannot represent a real security")
    root=Path(__file__).resolve().parents[1]; fixture=root/"tests"/"fixtures"
    market=json.loads((fixture/"alpha_vantage_daily.synthetic.json").read_text())
    secfacts=json.loads((fixture/"sec_companyfacts.synthetic.json").read_text()); submissions=json.loads((fixture/"sec_submissions.synthetic.json").read_text())
    out=build_research_snapshot(symbol=args.symbol,market_data={"source":"alpha_vantage","source_url":"https://www.alphavantage.co/query","rows":[{"symbol":"TEST","as_of":d,"timestamp":d+"T00:00:00Z","open":float(v["1. open"]),"high":float(v["2. high"]),"low":float(v["3. low"]),"close":float(v["4. close"]),"volume":int(v["5. volume"]),"adjusted_close":None,"currency":None,"source":"alpha_vantage","source_url":"https://www.alphavantage.co/query","retrieved_at":"2024-01-04T00:00:00Z"} for d,v in market["Time Series (Daily)"].items()]},company_facts=secfacts,filings=submissions,as_of=args.as_of,data_mode="synthetic",snapshot_id="snapshot-fixture",run_id="run-fixture",clock=lambda:"2024-01-04T00:00:00Z")
    text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=False)+"\n";
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc: print(f"error: {exc}",file=sys.stderr); raise SystemExit(2)
