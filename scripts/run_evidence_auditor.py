#!/usr/bin/env python3
"""Prepare or explicitly run the offline Evidence Auditor PoC."""
from __future__ import annotations
import argparse, json, pathlib, time
from finsight_app.evidence_auditor import EvidenceAuditor, EvidenceAuditError, EvidenceAuditRunError
from finsight_app.ollama_client import OllamaClient, OllamaError

class RecordingOllamaClient(OllamaClient):
    """Capture the exact request and raw response without changing the client."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests = []
        self.responses = []
        self.last_generation = None
    def _request(self, method, path, payload=None):
        if method == "POST" and path == "/api/chat":
            self.requests.append(payload)
        response = super()._request(method, path, payload)
        if method == "POST" and path == "/api/chat":
            self.responses.append(response)
        return response
    def generate(self, messages, schema):
        result = super().generate(messages, schema)
        self.last_generation = dict(result)
        return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--run-model", action="store_true")
    parser.add_argument("--output-dir", type=pathlib.Path)
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--expected-digest")
    args = parser.parse_args()
    if args.run_model and args.output_dir is None:
        print(json.dumps({"status":"failed","error":"--output-dir is required with --run-model"}, ensure_ascii=False))
        return 2
    if args.output_dir and args.output_dir.exists() and any(args.output_dir.iterdir()):
        print(json.dumps({"status":"failed","error":"output directory must be empty"}, ensure_ascii=False))
        return 2
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    client = None
    auditor = None
    started = time.monotonic()
    result = None
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        client = RecordingOllamaClient(model=args.model) if args.run_model else None
        auditor = EvidenceAuditor(client)
        messages, schema = auditor.prepare_request(payload)
        if args.output_dir:
            (args.output_dir / "request.json").write_text(json.dumps({"model":args.model,"messages":messages,"stream":False,"think":False,"format":schema}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        result = {"mode": "model" if args.run_model else "prepare", "external_network_executed": False,
                  "model_calls": 0, "request": {"messages": messages, "schema": schema}}
        if args.run_model:
            info = client.check_model()
            result["model"] = info["name"]; result["model_digest"] = info["digest"]
            if args.output_dir:
                (args.output_dir / "model-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            if args.expected_digest and info["digest"] != args.expected_digest:
                raise EvidenceAuditRunError("model digest mismatch")
            try:
                result["audit"] = auditor.run_model(payload)
                result["model_calls"] = auditor.model_call_count
                if args.expected_digest and client.last_generation and client.last_generation.get("model_digest") != args.expected_digest:
                    raise EvidenceAuditRunError("model digest changed during request")
                result["validation"] = "passed"
            except Exception as exc:
                result["validation"] = "failed"
                result["error_type"] = type(exc).__name__
                result["error"] = str(exc)
                result["model_calls"] = auditor.model_call_count
                raise
    except (OSError, json.JSONDecodeError, EvidenceAuditError, EvidenceAuditRunError, OllamaError) as exc:
        result = {"status": "failed", "error_type": type(exc).__name__, "error": str(exc),
                  "model_calls": getattr(auditor, "model_call_count", 0)}
    finally:
        elapsed = round((time.monotonic() - started) * 1000, 3)
        if result is None: result = {"status": "failed", "error_type": "unknown", "model_calls": 0}
        result.setdefault("status", "completed"); result["elapsed_ms"] = elapsed
        result.setdefault("external_network_executed", False)
        result["model_calls"] = getattr(auditor, "model_call_count", 0)
        if client is not None and getattr(client, "last_generation", None):
            result["generation"] = {k: client.last_generation.get(k) for k in ("model", "model_digest", "total_duration_ms", "done_reason")}
        if args.output_dir:
            (args.output_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            (args.output_dir / "raw-responses.json").write_text(json.dumps(getattr(client, "responses", []), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if result.get("status") == "failed":
        print(json.dumps({k: result.get(k) for k in ("status","error_type","model_calls","elapsed_ms")}, ensure_ascii=False)); return 2
    print(json.dumps({k: result.get(k) for k in ("status","mode","model_calls","elapsed_ms")}, ensure_ascii=False)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
