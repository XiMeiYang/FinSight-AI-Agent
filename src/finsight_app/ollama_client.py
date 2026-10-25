"""Small, fail-safe client for a local Ollama structured-output endpoint."""
from __future__ import annotations

import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler


class OllamaError(RuntimeError):
    """Base class for local Ollama failures."""


class OllamaUnavailable(OllamaError): pass
class OllamaModelMissing(OllamaError): pass
class OllamaTimeout(OllamaError): pass
class OllamaProtocolError(OllamaError): pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OllamaProtocolError("redirects are not allowed")


class OllamaClient:
    def __init__(self, model: str = "qwen3:4b", base_url: str = "http://127.0.0.1:11434", timeout: float = 120):
        if not isinstance(model, str) or not model.strip() or any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in model):
            raise ValueError("model must be a non-empty safe string")
        self.model = model
        self.base_url = self._validate_base_url(base_url)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 600:
            raise ValueError("timeout must be between 0 and 600 seconds")
        self.timeout = float(timeout)
        self.chat_request_count = 0
        # An empty ProxyHandler prevents HTTP_PROXY/HTTPS_PROXY environment
        # variables from routing even loopback traffic through a proxy.
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())

    @staticmethod
    def _validate_base_url(value: str) -> str:
        try: parsed = urlsplit(value)
        except Exception as exc: raise ValueError("invalid Ollama URL") from exc
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username or parsed.password:
            raise ValueError("Ollama URL must be local HTTP")
        if parsed.port != 11434 or parsed.query or parsed.fragment or parsed.path.rstrip("/") not in {"",}:
            raise ValueError("Ollama URL must target port 11434 without a path")
        return "http://127.0.0.1:11434"

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = Request(self.base_url + path, data=data, method=method,
                          headers={"Accept": "application/json", "Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise OllamaProtocolError("Ollama response is too large")
        except HTTPError as exc:
            if exc.code == 404 and path == "/api/tags": raise OllamaUnavailable("Ollama API unavailable") from None
            raise OllamaProtocolError("Ollama request failed") from None
        except (socket.timeout, TimeoutError):
            raise OllamaTimeout("Ollama request timed out") from None
        except (URLError, OSError):
            raise OllamaUnavailable("Ollama is unavailable") from None
        try: result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OllamaProtocolError("Ollama returned malformed JSON") from None
        if not isinstance(result, dict): raise OllamaProtocolError("Ollama response must be an object")
        return result

    def check_model(self) -> dict[str, str]:
        payload = self._request("GET", "/api/tags")
        models = payload.get("models")
        if not isinstance(models, list): raise OllamaProtocolError("Ollama tags response is invalid")
        for item in models:
            if isinstance(item, dict) and item.get("name") == self.model:
                digest = item.get("digest")
                if not isinstance(digest, str) or not digest: raise OllamaProtocolError("Ollama model digest is missing")
                return {"name": self.model, "digest": digest}
        raise OllamaModelMissing("Ollama model is not installed")

    def generate(self, messages: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(messages, list) or not all(isinstance(x, dict) for x in messages):
            raise ValueError("messages must be a list of objects")
        if not isinstance(schema, dict) or schema.get("type", "object") != "object":
            raise ValueError("schema must be an object schema")
        model_info = self.check_model()
        self.chat_request_count += 1
        response = self._request("POST", "/api/chat", {"model": self.model, "messages": messages,
            "stream": False, "think": False, "format": schema})
        message = response.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not isinstance(response.get("done"), bool) or not response["done"]:
            raise OllamaProtocolError("Ollama returned an incomplete response")
        reason = response.get("done_reason")
        if reason != "stop":
            # A length stop means the structured answer may be truncated;
            # unknown reasons are likewise unsafe to expose as complete.
            raise OllamaProtocolError("Ollama response did not stop normally")
        def integer(name):
            value = response.get(name)
            return value if isinstance(value, int) and not isinstance(value, bool) else None
        duration = response.get("total_duration")
        duration_ms = duration // 1_000_000 if isinstance(duration, int) else None
        return {"content": content, "model": self.model, "model_digest": model_info["digest"],
                "total_duration_ms": duration_ms, "prompt_eval_count": integer("prompt_eval_count"),
                "eval_count": integer("eval_count"), "done": True, "done_reason": reason}
