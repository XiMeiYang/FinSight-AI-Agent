"""Minimal CLI for an explicitly enabled SEC smoke check."""
import argparse, json
from .client import SECClient, SECConfig
def main():
    p=argparse.ArgumentParser(); p.add_argument("ticker"); p.add_argument("--as-of"); a=p.parse_args()
    c=SECClient(SECConfig.from_environment()); cik=c.ticker_to_cik(a.ticker); payload,raw,url=c.company_facts(cik)
    result=c.normalize_facts(payload, as_of=a.as_of, source_url=url, raw_sha256=c.raw_sha256(raw)); print(json.dumps({"cik":result.cik,"facts":len(result.facts),"raw_sha256":result.raw_sha256}, ensure_ascii=False))
if __name__ == "__main__": main()
