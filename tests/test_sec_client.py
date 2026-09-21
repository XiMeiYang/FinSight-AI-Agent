import json, os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from finsight_sec.client import SECClient, SECConfig, SECError, SECRequestError

class Response:
    def __init__(self, data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self): return self.data

class TestSEC(unittest.TestCase):
    def setUp(self): self.sleep=[]
    def test_user_agent_required(self):
        with self.assertRaises(SECError): SECClient(SECConfig(user_agent=None)).ticker_to_cik("AAPL")
    def test_ticker_mapping_and_zero_pad(self):
        c=SECClient(SECConfig(user_agent="test test@example.com")); self.assertEqual(c.ticker_to_cik(" aapl ", {"AAPL":"320193"}), "0000320193")
    def test_normalize_and_as_of_filter_and_hash(self):
        p={"cik":320193,"entityName":"Example","facts":{"us-gaap":{"Revenue":{"label":"Revenue","units":{"USD":[{"val":10,"end":"2023-12-31","filed":"2024-02-01","form":"10-K","accn":"x"},{"val":11,"end":"2024-12-31","filed":"2025-02-01","form":"10-K","accn":"y"}]}}}}}
        out=SECClient.normalize_facts(p,as_of="2024-12-31"); self.assertEqual(len(out.facts),1); self.assertEqual(out.cik,"0000320193"); self.assertEqual(len(out.raw_sha256),64)
    def test_select_filings(self):
        s={"cik":320193,"filings":{"recent":{"form":["10-K","8-K","10-Q"],"filingDate":["2024-02-01","2025-01-01","2024-05-01"],"reportDate":["2023-12-31"]*3,"acceptanceDateTime":[None]*3,"accessionNumber":["000-1","000-2","000-3"],"primaryDocument":["a.htm","b.htm","c.htm"]}}}
        fs=SECClient.select_filings(s, forms=["10-K","10-Q"], as_of="2024-12-31"); self.assertEqual([x.form for x in fs],["10-K","10-Q"]); self.assertIn("Archives",fs[0].filing_url)
    def test_http_classification_and_retry(self):
        from urllib.error import HTTPError
        calls=[]
        def opener(req,timeout):
            calls.append(1)
            if len(calls)==1: raise HTTPError(req.full_url,429,"",{},None)
            return Response(b'{"values":{}}')
        c=SECClient(SECConfig(user_agent="test test@example.com",sleep=lambda n:self.sleep.append(n),min_interval_seconds=0,max_retries=1),opener)
        self.assertEqual(c._get_json("/x")[0],{"values":{}}); self.assertEqual(len(calls),2)
    def test_raw_download_preserves_bytes_and_hash(self):
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0),lambda req,timeout: Response(b"<html>raw</html>"))
        raw,digest=c.download_raw("https://www.sec.gov/Archives/example.htm"); self.assertEqual(raw,b"<html>raw</html>"); self.assertEqual(digest,c.raw_sha256(raw))
    def test_raw_download_blocks_external_url(self):
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0))
        with self.assertRaises(SECRequestError) as cm: c.download_raw("https://example.com/x")
        self.assertEqual(cm.exception.category,"blocked_url")
    def test_raw_download_retries_429(self):
        from urllib.error import HTTPError
        calls=[]
        def opener(req,timeout):
            calls.append(1)
            if len(calls)<2: raise HTTPError(req.full_url,429,"",{},None)
            return Response(b"ok")
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0,max_retries=1,sleep=lambda _:None),opener)
        self.assertEqual(c.download_raw("https://www.sec.gov/Archives/x")[0],b"ok"); self.assertEqual(len(calls),2)
    def test_timeout_retries_then_stops(self):
        calls=[]
        def opener(req,timeout): calls.append(1); raise TimeoutError()
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0,max_retries=1,sleep=lambda _:None),opener)
        with self.assertRaises(SECRequestError) as cm: c._get_json("/x")
        self.assertEqual(cm.exception.category,"timeout"); self.assertEqual(len(calls),2)
    def test_5xx_retries_then_stops(self):
        from urllib.error import HTTPError
        calls=[]
        def opener(req,timeout): calls.append(1); raise HTTPError(req.full_url,503,"",{},None)
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0,max_retries=1,sleep=lambda _:None),opener)
        with self.assertRaises(SECRequestError) as cm: c._get_json("/x")
        self.assertEqual(cm.exception.category,"server_error"); self.assertEqual(len(calls),2)
    def test_4xx_does_not_retry(self):
        from urllib.error import HTTPError
        calls=[]
        def opener(req,timeout): calls.append(1); raise HTTPError(req.full_url,404,"",{},None)
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0,max_retries=3,sleep=lambda _:None),opener)
        with self.assertRaises(SECRequestError) as cm: c._get_json("/x")
        self.assertEqual(cm.exception.category,"http_error"); self.assertEqual(len(calls),1)
    def test_invalid_json(self):
        c=SECClient(SECConfig(user_agent="test test@example.com",min_interval_seconds=0),lambda req,timeout: Response(b"bad"))
        with self.assertRaises(SECRequestError) as cm: c._get_json("/x")
        self.assertEqual(cm.exception.category,"invalid_payload")
    def test_save_payloads_idempotent_and_separated(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            c=SECClient(); raw=b"raw"; a=c.save_payloads(cik="1",kind="facts",raw=raw,normalized={"x":1},retrieved_at="20260101",root=d); b=c.save_payloads(cik="1",kind="facts",raw=raw,normalized={"x":2},retrieved_at="20260101",root=d)
            self.assertEqual(a,b); self.assertEqual(a[0].read_bytes(),raw); self.assertNotEqual(a[0],a[1]); self.assertIn('"x": 1',a[1].read_text())

if __name__ == "__main__": unittest.main()
