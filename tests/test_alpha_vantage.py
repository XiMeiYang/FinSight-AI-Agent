import json, sys, tempfile, unittest
from pathlib import Path
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from finsight_market.alpha_vantage import AlphaVantageClient, AlphaVantageConfig, MarketDataError

class Response:
    def __init__(self, data, url="https://www.alphavantage.co/query", status=200): self.data=data; self.url=url; self.status=status
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self): return self.data
    def geturl(self): return self.url

class TestAlphaVantage(unittest.TestCase):
    def fixture(self): return json.loads(Path(__file__).parent.joinpath("fixtures/alpha_vantage_daily.synthetic.json").read_text())
    def test_key_missing_stops(self):
        with self.assertRaisesRegex(MarketDataError, "API_KEY"): AlphaVantageClient(AlphaVantageConfig(api_key=None)).fetch_daily("AAPL")
    def test_normalize_sorted_decimal_and_fields(self):
        out=AlphaVantageClient.normalize(self.fixture(), symbol="test", source_url="fixture", retrieved_at="2026-09-21T00:00:00Z")
        self.assertEqual([r["as_of"] for r in out["rows"]], ["2024-01-02","2024-01-03"]); self.assertEqual(out["rows"][0]["volume"],90); self.assertIsNone(out["rows"][0]["adjusted_close"])
    def test_fetch_metadata_redacts_key(self):
        c=AlphaVantageClient(AlphaVantageConfig(api_key="secret",max_retries=0), lambda req,timeout: Response(json.dumps(self.fixture()).encode()))
        result=c.fetch_daily("test"); self.assertNotIn("secret", json.dumps(result["metadata"])); self.assertEqual(result["metadata"]["http_status"],200)
    def test_bad_range_and_empty(self):
        p=self.fixture(); p["Time Series (Daily)"]["2024-01-02"]["2. high"]="7"
        with self.assertRaisesRegex(MarketDataError,"relationship"): AlphaVantageClient.normalize(p,symbol="T")
        with self.assertRaises(MarketDataError): AlphaVantageClient.normalize({"Note":"limit"},symbol="T")
    def test_retry_429_and_stop_4xx_5xx_timeout(self):
        calls=[]
        def opener(req,timeout):
            calls.append(1)
            if len(calls)==1: raise HTTPError(req.full_url,429,"",{},None)
            return Response(json.dumps(self.fixture()).encode())
        c=AlphaVantageClient(AlphaVantageConfig(api_key="x",max_retries=1,sleep=lambda _:None),opener); c.fetch_daily("T"); self.assertEqual(len(calls),2); self.assertEqual(c.request_metadata[0]["retry_count"],0)
    def test_save_idempotent_separated(self):
        with tempfile.TemporaryDirectory() as d:
            a=AlphaVantageClient.save_payloads(symbol="T",raw=b"raw",normalized={"x":1},retrieved_at="2026",root=d); b=AlphaVantageClient.save_payloads(symbol="T",raw=b"raw",normalized={"x":2},retrieved_at="2026",root=d)
            self.assertEqual(a,b); self.assertNotEqual(a[0],a[1]); self.assertIn('"x": 1',a[1].read_text())

    def test_provider_note_retries(self):
        calls=[]
        def opener(req,timeout):
            calls.append(1); return Response(json.dumps({"Note":"slow"} if len(calls)==1 else self.fixture()).encode())
        c=AlphaVantageClient(AlphaVantageConfig(api_key="x",max_retries=1,sleep=lambda _:None),opener); c.fetch_daily("T")
        self.assertEqual(len(calls),2); self.assertEqual(c.request_metadata[0]["retry_reason"],"rate_limited")
    def test_4xx_5xx_timeout_invalid_json_redirect(self):
        for exc,cat,retries in [(HTTPError("x",400,"",{},None),"http_error",1),(HTTPError("x",500,"",{},None),"server_error",2),(TimeoutError(),"timeout",2)]:
            calls=[]
            def opener(req,timeout,exc=exc): calls.append(1); raise exc
            c=AlphaVantageClient(AlphaVantageConfig(api_key="x",max_retries=1,sleep=lambda _:None),opener)
            with self.assertRaises(MarketDataError) as e: c.fetch_daily("T")
            self.assertEqual(e.exception.category,cat); self.assertEqual(len(calls),retries)
        with self.assertRaises(MarketDataError): AlphaVantageClient(AlphaVantageConfig(api_key="x"),lambda req,timeout: Response(b"bad")).fetch_daily("T")
        with self.assertRaises(MarketDataError) as e: AlphaVantageClient(AlphaVantageConfig(api_key="x"),lambda req,timeout: Response(b"{}","https://example.com")).fetch_daily("T")
        self.assertEqual(e.exception.category,"blocked_url")
    def test_strict_normalization_boundaries(self):
        p=self.fixture(); p["Time Series (Daily)"]={}
        with self.assertRaises(MarketDataError): AlphaVantageClient.normalize(p,symbol="T")
        for key,val,cat in [("1. open","-1","invalid_range"),("1. open","NaN","invalid_type"),("5. volume","1.2","invalid_type")]:
            p=self.fixture(); p["Time Series (Daily)"]["2024-01-02"][key]=val
            with self.assertRaises(MarketDataError) as e: AlphaVantageClient.normalize(p,symbol="T")
            self.assertEqual(e.exception.category,cat)
        p=self.fixture(); p["Time Series (Daily)"]={"2024-02-30":p["Time Series (Daily)"]["2024-01-02"]}
        with self.assertRaises(MarketDataError) as e: AlphaVantageClient.normalize(p,symbol="T")
        self.assertEqual(e.exception.category,"invalid_date")
    def test_duplicate_date_and_runner_no_network(self):
        p=self.fixture(); p["Time Series (Daily)"]["2024-01-03"]=p["Time Series (Daily)"]["2024-01-02"]
        self.assertEqual(len(AlphaVantageClient.normalize(p,symbol="T")["rows"]), 2)
        import subprocess
        r=subprocess.run([sys.executable,"scripts/run_market_poc.py","T"],capture_output=True,text=True)
        self.assertEqual(r.returncode,2); self.assertIn("network disabled",r.stderr)

if __name__ == "__main__": unittest.main()
