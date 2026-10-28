import json
import unittest
import tempfile
from pathlib import Path
import subprocess
import sys
import os
import importlib
import contextlib
import io
import re
from unittest import mock
from unittest.mock import Mock

from finsight_app.evidence_auditor import EvidenceAuditor, EvidenceAuditError, EvidenceAuditRunError, system_prompt_sha256

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

    def test_prompt_versions_are_explicit_and_hashed(self):
        baseline = EvidenceAuditor().prepare_request(payload())[0][0]["content"]
        candidate = EvidenceAuditor(prompt_version="candidate-v1").prepare_request(payload())[0][0]["content"]
        self.assertNotEqual(baseline, candidate)
        self.assertEqual(system_prompt_sha256("baseline"), system_prompt_sha256("baseline"))
        self.assertNotEqual(system_prompt_sha256("baseline"), system_prompt_sha256("candidate-v1"))
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor(prompt_version="nope")

    def test_candidate_prompt_matches_document_blockquote_without_markers(self):
        doc = Path("docs/poc/evidence-auditor-prompt-candidate-v1.md").read_text(encoding="utf-8")
        block = doc.split("## 候选系统提示词全文", 1)[1].split("## 与当前默认提示词的差异", 1)[0]
        expected = "\n".join(
            re.sub(r"\*\*|`", "", line[2:] if line.startswith("> ") else "")
            for line in block.splitlines()
            if line.startswith(">")
        ).strip()
        from finsight_app.evidence_auditor import CANDIDATE_SYSTEM_PROMPT
        self.assertEqual(CANDIDATE_SYSTEM_PROMPT, expected)
    def test_isolated_requests_contain_only_their_target_pair(self):
        requests = EvidenceAuditor().prepare_isolated_requests(payload())
        self.assertEqual([x[0] for x in requests], ["P1", "P2"])
        for pair_id, messages, _schema in requests:
            body = json.loads(messages[1]["content"])
            self.assertEqual(len(body["pairs"]), 1)
            self.assertEqual(body["pairs"][0]["pair_id"], pair_id)
            other_id = "P2" if pair_id == "P1" else "P1"
            self.assertNotIn(other_id, messages[1]["content"])

    def test_run_model_rejects_multiple_pairs_before_call(self):
        client = Mock(); client.chat_request_count = 0
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor(client).run_model(payload())
        client.generate.assert_not_called()

    def test_cli_isolates_failure_and_persists_each_item(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.chat_request_count = 0; self.requests = []; self.responses = []; self.last_generation = None
            def check_model(self): return {"name": "synthetic", "digest": "digest"}
            def generate(self, messages, schema):
                self.requests.append({"messages": messages, "format": schema})
                self.chat_request_count += 1
                pair = json.loads(messages[1]["content"])["pairs"][0]
                if pair["pair_id"] == "P1":
                    response = {"message": {"content": '{"results":[{"pair_id":"P1","verdict":"supported","evidence_quote":"forged","reason_cn":"有依据"}]}'}, "done": True, "done_reason": "stop", "total_duration": 1000000}
                else:
                    response = {"message": {"content": json.dumps({"results":[{"pair_id":"P2","verdict":"unsupported","evidence_quote":"","reason_cn":"窗口不足"}]}, ensure_ascii=False)}, "done": True, "done_reason": "stop", "total_duration": 2000000}
                self.responses.append(response); self.last_generation = {"model_digest": "digest"}
                content = response["message"]["content"]
                return {"content": content, "model_digest": "digest", "total_duration_ms": response["total_duration"] // 1000000}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); inp = root / "pairs.json"; out = root / "out"
            inp.write_text(json.dumps(payload()), encoding="utf-8")
            with mock.patch.object(module, "RecordingOllamaClient", FakeClient), mock.patch.object(sys, "argv", ["run_evidence_auditor.py", str(inp), "--run-model", "--expected-digest", "digest", "--output-dir", str(out)]), contextlib.redirect_stdout(io.StringIO()) as stdout:
                code = module.main()
            self.assertEqual(code, 2)
            summary = json.loads((out / "result.json").read_text())
            self.assertEqual(summary["model_calls"], 2)
            self.assertEqual([x["status"] for x in summary["items"]], ["validation_failed", "accepted"])
            self.assertEqual(summary["status_counts"]["validation_failed"], 1)
            self.assertEqual(len(json.loads((out / "items" / "01" / "actual-requests.json").read_text())), 1)
            self.assertEqual(len(json.loads((out / "items" / "02" / "raw-responses.json").read_text())), 1)

    def test_cli_global_digest_failure_marks_all_not_executed(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class Missing:
            def __init__(self, *args, **kwargs): self.chat_request_count = 0; self.requests=[]; self.responses=[]; self.last_generation=None
            def check_model(self): raise RuntimeError("missing model")
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"pairs.json"; out=root/"out"; inp.write_text(json.dumps(payload()), encoding="utf-8")
            with mock.patch.object(module, "RecordingOllamaClient", Missing), mock.patch.object(sys, "argv", ["x", str(inp), "--run-model", "--expected-digest", "digest", "--output-dir", str(out)]), contextlib.redirect_stdout(io.StringIO()):
                code=module.main()
            self.assertEqual(code, 2)
            summary=json.loads((out/"result.json").read_text())
            self.assertEqual(summary["model_calls"], 0)
            self.assertEqual(summary["status_counts"]["not_executed"], 2)
            self.assertTrue(all(x["status"] == "not_executed" for x in summary["items"]))

    def test_cli_post_failure_counts_call_and_continues(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class ProtocolFailClient:
            def __init__(self,*a,**k): self.chat_request_count=0; self.requests=[]; self.responses=[]; self.last_generation=None
            def check_model(self): return {"name":"synthetic","digest":"digest"}
            def generate(self,messages,schema):
                self.requests.append({"messages":messages}); self.chat_request_count += 1
                pid=json.loads(messages[1]["content"])["pairs"][0]["pair_id"]
                if pid == "P1":
                    self.responses.append({"done":False}); raise RuntimeError("protocol failure")
                self.responses.append({"done":True,"total_duration":1})
                self.last_generation={"model_digest":"digest"}
                return {"content":json.dumps({"results":[{"pair_id":"P2","verdict":"unsupported","evidence_quote":"","reason_cn":"无依据"}]})}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"pairs.json"; out=root/"out"; inp.write_text(json.dumps(payload()), encoding="utf-8")
            with mock.patch.object(module,"RecordingOllamaClient",ProtocolFailClient), mock.patch.object(sys,"argv",["x",str(inp),"--run-model","--expected-digest","digest","--output-dir",str(out)]), contextlib.redirect_stdout(io.StringIO()):
                code=module.main()
            self.assertEqual(code,2)
            summary=json.loads((out/"result.json").read_text())
            self.assertEqual(summary["model_calls"],2)
            self.assertEqual(summary["items"][0]["request_count"],1)
            self.assertEqual(summary["items"][0]["model_calls"],1)
            self.assertEqual(summary["items"][1]["status"],"accepted")
            self.assertIsNone(summary["items"][0]["model_digest"])

    def test_cli_preflight_digest_mismatch_marks_all_without_calls(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class DigestClient:
            def __init__(self,*a,**k): self.chat_request_count=0; self.requests=[]; self.responses=[]; self.last_generation=None
            def check_model(self): return {"name":"synthetic","digest":"actual"}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"pairs.json"; out=root/"out"; inp.write_text(json.dumps(payload()), encoding="utf-8")
            with mock.patch.object(module,"RecordingOllamaClient",DigestClient), mock.patch.object(sys,"argv",["x",str(inp),"--run-model","--expected-digest","expected","--output-dir",str(out)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(),2)
            summary=json.loads((out/"result.json").read_text())
            self.assertEqual(summary["model_calls"],0)
            self.assertEqual([x["status"] for x in summary["items"]],["not_executed","not_executed"])
            self.assertEqual(json.loads((out/"items"/"01"/"raw-responses.json").read_text()),[])

    def test_cli_wrong_pair_id_isolated_failure_keeps_next_item(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class WrongIdClient:
            def __init__(self,*a,**k): self.chat_request_count=0; self.requests=[]; self.responses=[]; self.last_generation=None
            def check_model(self): return {"name":"synthetic","digest":"digest"}
            def generate(self,messages,schema):
                self.requests.append({"messages":messages}); self.chat_request_count += 1
                pid=json.loads(messages[1]["content"])["pairs"][0]["pair_id"]
                out_pid="BAD" if pid == "P1" else "P2"
                content=json.dumps({"results":[{"pair_id":out_pid,"verdict":"unsupported","evidence_quote":"","reason_cn":"无依据"}]})
                self.responses.append({"done":True,"total_duration":1}); self.last_generation={"model_digest":"digest"}
                return {"content":content}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"pairs.json"; out=root/"out"; inp.write_text(json.dumps(payload()), encoding="utf-8")
            with mock.patch.object(module,"RecordingOllamaClient",WrongIdClient), mock.patch.object(sys,"argv",["x",str(inp),"--run-model","--expected-digest","digest","--output-dir",str(out)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(),2)
            summary=json.loads((out/"result.json").read_text())
            self.assertEqual(summary["items"][0]["status"],"validation_failed")
            self.assertEqual(summary["items"][1]["status"],"accepted")
            self.assertEqual(summary["model_calls"],2)

    def test_cli_post_before_failure_has_zero_request_and_next_runs(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class BeforePostClient:
            def __init__(self,*a,**k): self.chat_request_count=0; self.requests=[]; self.responses=[]; self.last_generation=None
            def check_model(self): return {"name":"synthetic","digest":"digest"}
            def generate(self,messages,schema):
                pid=json.loads(messages[1]["content"])["pairs"][0]["pair_id"]
                if pid == "P1": raise RuntimeError("before post")
                self.requests.append({"messages":messages}); self.chat_request_count += 1; self.responses.append({"done":True,"total_duration":1}); self.last_generation={"model_digest":"digest"}
                return {"content":json.dumps({"results":[{"pair_id":"P2","verdict":"unsupported","evidence_quote":"","reason_cn":"无依据"}]})}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"pairs.json"; out=root/"out"; inp.write_text(json.dumps(payload()), encoding="utf-8")
            with mock.patch.object(module,"RecordingOllamaClient",BeforePostClient), mock.patch.object(sys,"argv",["x",str(inp),"--run-model","--expected-digest","digest","--output-dir",str(out)]), contextlib.redirect_stdout(io.StringIO()): self.assertEqual(module.main(),2)
            summary=json.loads((out/"result.json").read_text()); first=summary["items"][0]
            self.assertEqual(summary["model_calls"],1); self.assertEqual(first["request_count"],0); self.assertEqual(first["response_count"],0)
            self.assertEqual(json.loads((out/"items"/"01"/"actual-requests.json").read_text()),[])

    def test_cli_runtime_digest_change_stops_remaining_items(self):
        module = importlib.import_module("scripts.run_evidence_auditor")
        class ChangingDigestClient:
            def __init__(self,*a,**k): self.chat_request_count=0; self.requests=[]; self.responses=[]; self.last_generation=None
            def check_model(self): return {"name":"synthetic","digest":"digest"}
            def generate(self,messages,schema):
                self.requests.append({"messages":messages}); self.chat_request_count += 1; pid=json.loads(messages[1]["content"])["pairs"][0]["pair_id"]
                self.responses.append({"done":True,"total_duration":1}); self.last_generation={"model_digest":"changed" if pid == "P2" else "digest"}
                return {"content":json.dumps({"results":[{"pair_id":pid,"verdict":"unsupported","evidence_quote":"","reason_cn":"无依据"}]})}
        payload3={**payload(),"pairs":payload()["pairs"]+[dict(payload()["pairs"][0],pair_id="P3",evidence_id="E3")]}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"pairs.json"; out=root/"out"; inp.write_text(json.dumps(payload3), encoding="utf-8")
            with mock.patch.object(module,"RecordingOllamaClient",ChangingDigestClient), mock.patch.object(sys,"argv",["x",str(inp),"--run-model","--expected-digest","digest","--output-dir",str(out)]), contextlib.redirect_stdout(io.StringIO()): self.assertEqual(module.main(),2)
            summary=json.loads((out/"result.json").read_text()); self.assertEqual(summary["model_calls"],2)
            self.assertEqual([x["status"] for x in summary["items"]],["accepted","run_failed","not_executed"])
            self.assertEqual(summary["status_counts"]["not_executed"],1)
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
        client=Mock(); a=EvidenceAuditor(client); a.prepare_isolated_requests(payload()); self.assertEqual(a.model_call_count,0); client.generate.assert_not_called()
    def test_timeout_and_invalid_json(self):
        class Timeout:
            def generate(self,*args): raise TimeoutError()
        with self.assertRaises(EvidenceAuditRunError): EvidenceAuditor(Timeout()).run_model({"schema_version":"1.0","pairs":[payload()["pairs"][0]]})
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result("not json",payload()["pairs"])

    def test_failure_before_post_does_not_count_chat(self):
        class BeforePost:
            chat_request_count = 0
            def generate(self, *args):
                raise RuntimeError("model unavailable before POST")
        client = BeforePost()
        with self.assertRaises(EvidenceAuditRunError): EvidenceAuditor(client).run_model({"schema_version":"1.0","pairs":[payload()["pairs"][0]]})
        self.assertEqual(client.chat_request_count, 0)

    def test_protocol_truncation_failure_counts_only_actual_chat(self):
        class Truncated:
            chat_request_count = 0
            def generate(self, *args):
                from finsight_app.ollama_client import OllamaProtocolError
                self.chat_request_count += 1
                raise OllamaProtocolError("incomplete")
        auditor = EvidenceAuditor(Truncated())
        with self.assertRaises(EvidenceAuditRunError): auditor.run_model({"schema_version":"1.0","pairs":[payload()["pairs"][0]]})
        self.assertEqual(auditor.model_call_count, 1)

    def test_sequential_calls_accumulate_actual_chat_count(self):
        class Client:
            chat_request_count = 0
            def generate(self, messages, schema):
                self.chat_request_count += 1
                return {"content": json.dumps(self.good_result), "done": True}
            good_result = {"results": [{"pair_id": "P1", "verdict": "supported",
                "evidence_quote": "We use third parties to manufacture and assemble our products.", "reason_cn": "有依据。"}]}
        client = Client()
        auditor = EvidenceAuditor(client)
        auditor.run_model({"schema_version": "1.0", "pairs": [payload()["pairs"][0]]})
        auditor.run_model({"schema_version": "1.0", "pairs": [payload()["pairs"][0]]})
        self.assertEqual(client.chat_request_count, 2)
        self.assertEqual(auditor.model_call_count, 2)

    def test_cli_prepare_writes_safe_artifacts_without_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); inp = root / "pairs.json"; out = root / "out"
            inp.write_text(json.dumps(payload()), encoding="utf-8")
            env = dict(os.environ); env["PYTHONPATH"] = "src"
            proc = subprocess.run([sys.executable, "scripts/run_evidence_auditor.py", str(inp), "--output-dir", str(out)], capture_output=True, text=True, check=False, env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(proc.stdout)["model_calls"], 0)
            self.assertTrue((out / "items" / "01" / "request.json").exists())
            self.assertTrue((out / "items" / "02" / "request.json").exists())
            self.assertTrue((out / "raw-responses.json").exists())
            self.assertTrue((out / "result.json").exists())

    def test_cli_records_prompt_version_and_hash_without_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); inp = root / "pairs.json"; out = root / "out"
            inp.write_text(json.dumps(payload()), encoding="utf-8")
            env = dict(os.environ); env["PYTHONPATH"] = "src"
            proc = subprocess.run([sys.executable, "scripts/run_evidence_auditor.py", str(inp), "--prompt-version", "candidate-v1", "--output-dir", str(out)], capture_output=True, text=True, check=False, env=env)
            self.assertEqual(proc.returncode, 0)
            summary = json.loads((out / "result.json").read_text())
            request = json.loads((out / "items" / "01" / "request.json").read_text())
            self.assertEqual(summary["prompt_version"], "candidate-v1")
            self.assertEqual(summary["system_prompt_sha256"], request["system_prompt_sha256"])
            self.assertEqual(summary["model_calls"], 0)

    def test_cli_prompt_versions_use_separate_artifacts_and_reject_nonempty_dir(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); inp = root / "pairs.json"; baseline_dir = root / "baseline"; candidate_dir = root / "candidate"
            inp.write_text(json.dumps(payload()), encoding="utf-8")
            env = dict(os.environ); env["PYTHONPATH"] = "src"
            for version, out in (("baseline", baseline_dir), ("candidate-v1", candidate_dir)):
                proc = subprocess.run([sys.executable, "scripts/run_evidence_auditor.py", str(inp), "--prompt-version", version, "--output-dir", str(out)], capture_output=True, text=True, check=False, env=env)
                self.assertEqual(proc.returncode, 0)
            base = json.loads((baseline_dir / "result.json").read_text())
            cand = json.loads((candidate_dir / "result.json").read_text())
            base_req = json.loads((baseline_dir / "items" / "01" / "request.json").read_text())
            cand_req = json.loads((candidate_dir / "items" / "01" / "request.json").read_text())
            self.assertEqual(base["prompt_version"], "baseline")
            self.assertEqual(cand["prompt_version"], "candidate-v1")
            self.assertNotEqual(base["system_prompt_sha256"], cand["system_prompt_sha256"])
            self.assertEqual(base_req["format"], cand_req["format"])
            self.assertEqual(base_req["messages"][1], cand_req["messages"][1])
            nonempty = root / "nonempty"
            nonempty.mkdir(); (nonempty / "keep.json").write_text("{}", encoding="utf-8")
            rejected = subprocess.run([sys.executable, "scripts/run_evidence_auditor.py", str(inp), "--output-dir", str(nonempty)], capture_output=True, text=True, check=False, env=env)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual((nonempty / "keep.json").read_text(), "{}")
    def test_cross_window_quote_rejected(self):
        value=self.good(); value["results"][0]["evidence_quote"]="uncertain supply and capacity availability."
        with self.assertRaises(EvidenceAuditError): EvidenceAuditor.validate_result(value,payload()["pairs"])

if __name__ == "__main__": unittest.main()
