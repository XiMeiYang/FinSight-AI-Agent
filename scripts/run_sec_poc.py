"""Explicit SEC live flow. Stops before network when User-Agent is absent."""
import argparse, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from finsight_sec.client import SECClient, SECConfig, SECError

def main():
    p=argparse.ArgumentParser(); p.add_argument("--ticker",default="NVDA"); p.add_argument("--as-of"); a=p.parse_args()
    if not os.getenv("FINSIGHT_SEC_USER_AGENT"):
        print(json.dumps({"status":"stopped","reason":"FINSIGHT_SEC_USER_AGENT is not set","network_executed":False})); return 2
    started=time.monotonic(); c=SECClient(SECConfig.from_environment())
    try:
        ticker_payload,ticker_raw,ticker_url=c._get_json("/files/company_tickers.json"); c.save_payloads(cik="0000000000",kind="ticker_mapping",raw=ticker_raw,normalized=ticker_payload,retrieved_at=time.strftime("%Y%m%dT%H%M%SZ",time.gmtime()))
        cik=c.ticker_to_cik(a.ticker,ticker_payload and {str(v.get("ticker","" )).upper():str(v["cik_str"]).zfill(10) for v in ticker_payload.values()}); submissions_raw,submissions_bytes,submissions_url=c._get_json(f"/submissions/CIK{cik}.json"); c.save_payloads(cik=cik,kind="submissions",raw=submissions_bytes,normalized=submissions_raw,retrieved_at=time.strftime("%Y%m%dT%H%M%SZ",time.gmtime()))
        submissions=submissions_raw; raw_facts,raw,url=c.company_facts(cik)
        facts=c.normalize_facts(raw_facts,as_of=a.as_of,source_url=url,raw_sha256=c.raw_sha256(raw)); c.save_payloads(cik=cik,kind="companyfacts",raw=raw,normalized=facts,retrieved_at=facts.retrieved_at)
        filings=c.select_filings(submissions,as_of=a.as_of,retrieved_at=facts.retrieved_at)
        downloaded=None
        if filings:
            filing_raw, downloaded=c.download_raw(filings[0].filing_url); c.save_payloads(cik=cik,kind="filing_"+filings[0].form.replace("-",""),raw=filing_raw,normalized=filings[0],retrieved_at=facts.retrieved_at)
        print(json.dumps({"status":"success","ticker":a.ticker,"cik":cik,"filings":len(filings),"facts":len(facts.facts),"downloaded_bytes":len(filing_raw) if downloaded else 0,"downloaded_sha256":downloaded,"http_status":200,"attempts":c.attempts_total,"retries":max(0,c.attempts_total-3),"elapsed_seconds":round(time.monotonic()-started,3),"network_executed":True}))
        return 0
    except SECError as exc:
        print(json.dumps({"status":"failed","category":getattr(exc,"category",None),"error":str(exc),"attempts":c.attempts_total,"retries":max(0,c.attempts_total-1),"elapsed_seconds":round(time.monotonic()-started,3),"network_executed":True})); return 1
if __name__ == "__main__": raise SystemExit(main())
