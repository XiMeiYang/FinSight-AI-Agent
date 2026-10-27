import json
import unittest
import tempfile
from pathlib import Path
import subprocess
import sys
import os
from unittest.mock import Mock

from finsight_app.evidence_auditor import EvidenceAuditor, EvidenceAuditError, EvidenceAuditRunError

def payload():
    return {"schema_version":"1.0","data_mode":"synthetic","pairs":[
        {"pair_id":"P1","claim_text":"第三方制造","evidence_id":"E2","evidence_text":"We use third parties to manufacture and assemble our products.","source":{"symbol":"TEST","form":"10-Q","filing_date":"2024-11-20","accession_number":"synthetic-a","chunk_id":"synthetic-c2","source_url":"https://example.invalid/synthetic/a"}},
        {"pair_id":"P2","claim_text":"组件可用性","evidence_id":"E6","evidence_text":"uncertain supply and capacity availability.","source":{"symbol":"TEST","form":"10-Q","filing_date":"2025-05-28","accession_number":"synthetic-b","chunk_id":"synthetic-c6","source_url":"https://example.invalid/synthetic/b"}},]}

class AuditorTests(unittest.TestCase):
    def good(self): return {"results":[{"pair_id":"P1","verdict":"supported","evidence_quote":"We use third parties to manufacture and assemble our products.","reason_cn":"窗口直接支持。"},{"pair_id":"P2","verdict":"unsupported","evidence_quote":"","reason_cn":"窗口未提组件。"}]}
    def test_prepare_and_validate_sources(self):
        a=EvidenceAuditor(); req,s=a.prepare_request(payload()); self.assertEqual(len(req),2)
        self.assertIn("claim_text 和 evidence_text", req[0]["content"])
        out=a.validate_result(self.good(),payload()["pairs"]); self.assertEqual(out["results"][0]["source"]["accession_number"],"synthetic-a")
    def test_missing_duplicate_unknown_ids(self):
        for results in [[],[self.good()["results"][0],self.good()["results"][0]],[{"pair_id":"X","verdict":"unsupported","evidence_quote":"","reason_cn":"无"},self.good()["results"][1]]]:
            with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result({"results":results},payload()["pairs"])
        duplicate = payload(); duplicate["pairs"].append({**duplicate["pairs"][0], "pair_id": " P1 "})
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor().prepare_request(duplicate)
    def test_invalid_verdict_and_quotes(self):
        bad=self.good(); bad["results"][0]["verdict"]="maybe"
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result(bad,payload()["pairs"])
        bad=self.good(); bad["results"][0]["verdict"]=[]
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result(bad,payload()["pairs"])
        bad=self.good(); bad["results"][0]["evidence_quote"]="fabricated"
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result(bad,payload()["pairs"])
    def test_partial_and_contradicted_need_real_quote(self):
        for verdict in ("partially_supported","contradicted"):
            value=self.good(); value["results"][0]["verdict"]=verdict; value["results"][0]["evidence_quote"]=""
            with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result(value,payload()["pairs"])
    def test_default_does_not_call_model(self):
        client=Mock(); a=EvidenceAuditor(); a.prepare_request(payload()); self.assertEqual(a.model_call_count,0); client.generate.assert_not_called()
    def test_timeout_and_invalid_json(self):
        class Timeout:
            def generate(self,*args): raise TimeoutError()
        with self.assertRaises(EvidenceAuditRunError): EvidenceAuditor(Timeout()).run_model(payload())
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result("not json",payload()["pairs"])

    def test_failure_before_post_does_not_count_chat(self):
        class BeforePost:
            chat_request_count = 0
            def generate(self, *args):
                raise RuntimeError("model unavailable before POST")
        client = BeforePost()
        with self.assertRaises(EvidenceAuditRunError): EvidenceAuditor(client).run_model(payload())
        self.assertEqual(client.chat_request_count, 0)

    def test_protocol_truncation_failure_counts_only_actual_chat(self):
        class Truncated:
            chat_request_count = 0
            def generate(self, *args):
                from finsight_app.ollama_client import OllamaProtocolError
                self.chat_request_count += 1
                raise OllamaProtocolError("incomplete")
        auditor = EvidenceAuditor(Truncated())
        with self.assertRaises(EvidenceAuditRunError): auditor.run_model(payload())
        self.assertEqual(auditor.model_call_count, 1)

    def test_cli_prepare_writes_safe_artifacts_without_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); inp = root / "pairs.json"; out = root / "out"
            inp.write_text(json.dumps(payload()), encoding="utf-8")
            env = dict(os.environ); env["PYTHONPATH"] = "src"
            proc = subprocess.run([sys.executable, "scripts/run_evidence_auditor.py", str(inp), "--output-dir", str(out)], capture_output=True, text=True, check=False, env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(proc.stdout)["model_calls"], 0)
            self.assertTrue((out / "request.json").exists())
            self.assertTrue((out / "raw-responses.json").exists())
            self.assertTrue((out / "result.json").exists())
    def test_cross_window_quote_rejected(self):
        value=self.good(); value["results"][0]["evidence_quote"]="uncertain supply and capacity availability."
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result(value,payload()["pairs"])

if __name__ == "__main__": unittest.main()
