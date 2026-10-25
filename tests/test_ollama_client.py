import io
import json
import socket
import unittest
from unittest.mock import patch

from finsight_app.ollama_client import (
    OllamaClient, OllamaModelMissing, OllamaProtocolError, OllamaTimeout, _NoRedirect,
)


class Response:
    def __init__(self, payload): self.payload = json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, _limit=-1): return self.payload


class Opener:
    def __init__(self, responses): self.responses = iter(responses); self.requests = []
    def open(self, request, timeout): self.requests.append((request, timeout)); return Response(next(self.responses))


class OllamaClientTests(unittest.TestCase):
    def client(self, responses):
        opener = Opener(responses)
        with patch("finsight_app.ollama_client.build_opener", return_value=opener):
            client = OllamaClient(timeout=2)
        client._opener = opener
        return client, opener

    def test_rejects_non_loopback_urls(self):
        for url in ("https://127.0.0.1:11434", "http://localhost:11434", "http://127.0.0.1:11435", "http://127.0.0.1:11434/api", "http://u:p@127.0.0.1:11434"):
            with self.assertRaises(ValueError): OllamaClient(base_url=url)
        for model in ("", "  ", "qwen\n3:4b", "qwen\x004b"):
            with self.assertRaises(ValueError): OllamaClient(model=model)

    def test_http_and_https_redirects_are_rejected_before_target_request(self):
        class FakeRedirectOpener:
            def __init__(self): self.target_requests = 0
            def open(self, request, timeout):
                # Simulate a 302 Location response. The configured handler
                # must reject it before any request to the Location target.
                _NoRedirect().redirect_request(request, None, 302, "Found", {"Location": "https://example.invalid"}, "https://example.invalid")
                self.target_requests += 1

        opener = FakeRedirectOpener()
        with self.assertRaises(OllamaProtocolError):
            opener.open(None, 1)
        self.assertEqual(opener.target_requests, 0)
        with self.assertRaises(ValueError): OllamaClient(base_url="https://127.0.0.1:11434")

    def test_check_model_and_generate_schema(self):
        client, opener = self.client([
            {"models": [{"name": "qwen3:4b", "digest": "sha256:test"}]},
            {"message": {"content": '{"answer":"ok"}'}, "done": True, "done_reason": "stop",
             "total_duration": 3_000_000, "prompt_eval_count": 4, "eval_count": 5},
        ])
        result = client.generate([{"role": "user", "content": "question"}], {"type": "object", "properties": {}})
        self.assertEqual(result["model_digest"], "sha256:test")
        self.assertEqual(result["total_duration_ms"], 3)
        body = json.loads(opener.requests[1][0].data)
        self.assertEqual(body["stream"], False); self.assertEqual(body["think"], False)
        self.assertEqual(body["format"]["type"], "object")

    def test_missing_model_and_incomplete_response_fail(self):
        client, _ = self.client([{"models": []}])
        with self.assertRaises(OllamaModelMissing): client.check_model()
        missing_client, _ = self.client([{"models": []}])
        with self.assertRaises(OllamaModelMissing): missing_client.generate([], {"type": "object"})
        self.assertEqual(missing_client.chat_request_count, 0)
        client, _ = self.client([{"models": [{"name": "qwen3:4b", "digest": "d"}]}, {"done": False}])
        with self.assertRaises(OllamaProtocolError): client.generate([], {"type": "object"})
        self.assertEqual(client.chat_request_count, 1)
        client, _ = self.client([{"models": [{"name": "qwen3:4b", "digest": "d"}]},
                                 {"message": {"content": "partial"}, "done": True, "done_reason": "length"}])
        with self.assertRaises(OllamaProtocolError): client.generate([], {"type": "object"})

    def test_malformed_response_and_timeout_fail_safely(self):
        client, opener = self.client([])
        opener.open = lambda request, timeout: type("R", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "read": lambda s, limit: b"not-json"})()
        with self.assertRaises(OllamaProtocolError): client.check_model()
        opener.open = lambda request, timeout: (_ for _ in ()).throw(socket.timeout())
        with self.assertRaises(OllamaTimeout): client.check_model()

    def test_proxy_is_disabled_and_response_is_bounded(self):
        opener = Opener([])
        with patch("finsight_app.ollama_client.build_opener", return_value=opener) as factory:
            OllamaClient()
        self.assertEqual(factory.call_args.args[0].proxies, {})
        client, opener = self.client([])
        opener.open = lambda request, timeout: type("R", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "read": lambda s, limit: b"x" * (2 * 1024 * 1024 + 1)})()
        with self.assertRaises(OllamaProtocolError): client.check_model()


if __name__ == "__main__": unittest.main()
