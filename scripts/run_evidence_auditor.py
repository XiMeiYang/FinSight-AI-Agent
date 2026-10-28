#!/usr/bin/env python3
"""Prepare or explicitly run the offline Evidence Auditor PoC."""
from __future__ import annotations
import argparse, json, pathlib, time
from finsight_app.evidence_auditor import EvidenceAuditor, EvidenceAuditError, EvidenceAuditRunError, system_prompt_sha256
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
    parser.add_argument("--prompt-version", choices=("baseline", "candidate-v1"), default="baseline")
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
        auditor = EvidenceAuditor(client, prompt_version=args.prompt_version)
        isolated = auditor.prepare_isolated_requests(payload)
        prompt_hash = system_prompt_sha256(args.prompt_version)
        result = {"mode": "model" if args.run_model else "prepare", "external_network_executed": False,
                  "prompt_version": args.prompt_version, "system_prompt_sha256": prompt_hash,
                  "model_calls": 0, "pair_count": len(isolated), "items": [], "not_executed": []}
        for index, (pair_id, messages, schema) in enumerate(isolated, 1):
            if args.output_dir:
                item_dir = args.output_dir / "items" / f"{index:02d}"
                item_dir.mkdir(parents=True, exist_ok=True)
                (item_dir / "request.json").write_text(json.dumps({"model": args.model, "pair_id": pair_id,
                    "prompt_version": args.prompt_version, "system_prompt_sha256": prompt_hash,
                    "messages": messages, "stream": False, "think": False, "format": schema},
                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.run_model:
            result["not_executed"] = [x[0] for x in isolated]
            result["status"] = "prepared"
            result["status_counts"] = {"accepted": 0, "validation_failed": 0, "run_failed": 0, "not_executed": len(isolated)}
        if args.run_model:
            try:
                info = client.check_model()
            except Exception as exc:
                result["status"] = "failed"
                result["global_failure"] = type(exc).__name__
                result["error"] = "global model condition failed"
                result["not_executed"] = [x[0] for x in isolated]
                result["status_counts"] = {"accepted": 0, "validation_failed": 0, "run_failed": 0, "not_executed": len(isolated)}
                info = None
            if info is None:
                for index, (pair_id, _messages, _schema) in enumerate(isolated, 1):
                    item = {"pair_id": pair_id, "status": "not_executed", "prompt_version": args.prompt_version,
                            "system_prompt_sha256": prompt_hash, "model_calls": 0,
                            "request_count": 0, "response_count": 0, "elapsed_ms": 0,
                            "model_digest": None, "response_duration_ms": None,
                            "error": "global model condition failed"}
                    result["items"].append(item)
                    if args.output_dir:
                        item_dir = args.output_dir / "items" / f"{index:02d}"
                        (item_dir / "result.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        (item_dir / "actual-requests.json").write_text("[]\n", encoding="utf-8")
                        (item_dir / "raw-responses.json").write_text("[]\n", encoding="utf-8")
                raise EvidenceAuditRunError("global model condition failed")
            result["model"] = info["name"]; result["model_digest"] = info["digest"]
            if args.output_dir:
                (args.output_dir / "model-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            if args.expected_digest and info["digest"] != args.expected_digest:
                result["status"] = "failed"
                result["global_failure"] = "model_digest_mismatch"
                result["error"] = "global model condition failed"
                result["not_executed"] = [x[0] for x in isolated]
                result["status_counts"] = {"accepted": 0, "validation_failed": 0, "run_failed": 0, "not_executed": len(isolated)}
                for index, (pair_id, _messages, _schema) in enumerate(isolated, 1):
                    item = {"pair_id": pair_id, "status": "not_executed", "prompt_version": args.prompt_version,
                            "system_prompt_sha256": prompt_hash, "model_calls": 0,
                            "request_count": 0, "response_count": 0, "elapsed_ms": 0,
                            "model_digest": info["digest"], "response_duration_ms": None,
                            "error": "global model condition failed"}
                    result["items"].append(item)
                    if args.output_dir:
                        item_dir = args.output_dir / "items" / f"{index:02d}"
                        (item_dir / "result.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        (item_dir / "actual-requests.json").write_text("[]\n", encoding="utf-8")
                        (item_dir / "raw-responses.json").write_text("[]\n", encoding="utf-8")
                raise EvidenceAuditRunError("model digest mismatch")
            pair_by_id = {pair["pair_id"]: pair for pair in payload["pairs"]}
            for index, (pair_id, _messages, _schema) in enumerate(isolated, 1):
                item_started = time.monotonic()
                before_calls = client.chat_request_count
                before_requests = len(client.requests)
                before_responses = len(client.responses)
                previous_generation = client.last_generation
                item = {"pair_id": pair_id, "status": "accepted", "prompt_version": args.prompt_version,
                        "system_prompt_sha256": prompt_hash}
                try:
                    item["audit"] = auditor.run_model({"schema_version": "1.0", "pairs": [pair_by_id[pair_id]]})
                    if args.expected_digest and client.last_generation is not previous_generation and client.last_generation and client.last_generation.get("model_digest") != args.expected_digest:
                        raise EvidenceAuditRunError("model digest changed during request")
                except EvidenceAuditError as exc:
                    item.update({"status": "validation_failed", "error_type": type(exc).__name__, "error": str(exc)})
                except Exception as exc:
                    item.update({"status": "run_failed", "error_type": type(exc).__name__, "error": str(exc)})
                item["model_calls"] = client.chat_request_count - before_calls
                item["request_count"] = len(client.requests) - before_requests
                item["response_count"] = len(client.responses) - before_responses
                item["elapsed_ms"] = round((time.monotonic() - item_started) * 1000, 3)
                current_generation = client.last_generation
                item["model_digest"] = (current_generation.get("model_digest")
                                         if item["response_count"] and isinstance(current_generation, dict)
                                         and current_generation is not previous_generation else None)
                new_responses = client.responses[before_responses:]
                item["response_duration_ms"] = (new_responses[-1].get("total_duration", 0) // 1_000_000
                                                  if new_responses and isinstance(new_responses[-1].get("total_duration"), int) else None)
                result["items"].append(item)
                if args.output_dir:
                    item_dir = args.output_dir / "items" / f"{index:02d}"
                    (item_dir / "result.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    (item_dir / "actual-requests.json").write_text(json.dumps(client.requests[before_requests:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    (item_dir / "raw-responses.json").write_text(json.dumps(new_responses, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                if item["status"] == "run_failed" and "digest" in str(item.get("error", "")):
                    result["not_executed"] = [x[0] for x in isolated[index:]]
                    for remaining_index, (remaining_id, _rm, _rs) in enumerate(isolated[index:], index + 1):
                        remaining = {"pair_id": remaining_id, "status": "not_executed", "prompt_version": args.prompt_version,
                                     "system_prompt_sha256": prompt_hash, "model_calls": 0,
                                     "request_count": 0, "response_count": 0, "elapsed_ms": 0,
                                     "model_digest": None, "response_duration_ms": None,
                                     "error": "global model condition failed"}
                        result["items"].append(remaining)
                        if args.output_dir:
                            remaining_dir = args.output_dir / "items" / f"{remaining_index:02d}"
                            (remaining_dir / "result.json").write_text(json.dumps(remaining, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                            (remaining_dir / "actual-requests.json").write_text("[]\n", encoding="utf-8")
                            (remaining_dir / "raw-responses.json").write_text("[]\n", encoding="utf-8")
                    break
            result["model_calls"] = client.chat_request_count
            counts = {status: sum(x["status"] == status for x in result["items"])
                      for status in ("accepted", "validation_failed", "run_failed")}
            counts["not_executed"] = len(result["not_executed"])
            result["status_counts"] = counts
            result["status"] = "completed" if all(x["status"] == "accepted" for x in result["items"]) else "partial_failure"
    except (OSError, json.JSONDecodeError, EvidenceAuditError, EvidenceAuditRunError, OllamaError) as exc:
        if not isinstance(result, dict) or result.get("status") != "failed":
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
    if result.get("status") in {"failed", "partial_failure"}:
        print(json.dumps({k: result.get(k) for k in ("status","error_type","model_calls","elapsed_ms")}, ensure_ascii=False)); return 2
    print(json.dumps({k: result.get(k) for k in ("status","mode","model_calls","elapsed_ms")}, ensure_ascii=False)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
