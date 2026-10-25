from __future__ import annotations

from pathlib import Path
from typing import Optional
import unicodedata

try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field, field_validator
except ImportError:  # pragma: no cover - gives a useful install hint to the CLI
    FastAPI = None
    class BaseModel:  # keeps module importable for environments before app extras install
        pass
    def Field(*args, **kwargs): return None
    class Query:  # pragma: no cover
        def __init__(self, default=None, **kwargs): self.default = default

    class HTTPException(Exception):
        def __init__(self, status_code, detail): self.status_code, self.detail = status_code, detail

    StaticFiles = None

from finsight_rag.ingestion import parse_time
from .retrieval_service import RetrievalService
from .answer_service import AnswerGenerationError, AnswerValidationError
from .ollama_client import OllamaError, OllamaModelMissing, OllamaTimeout, OllamaUnavailable


class EvidenceRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)
    question: str = Field(min_length=3, max_length=1000)
    form: Optional[str] = None
    as_of: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=10)

    if FastAPI is not None:
        @field_validator("symbol")
        def normalize_symbol(cls, value): return value.strip().upper()

        @field_validator("question")
        def non_blank_question(cls, value):
            value = value.strip()
            if len(value) < 3: raise ValueError("question must contain at least three characters")
            return value

        @field_validator("form")
        def normalize_form(cls, value):
            if value is None: return value
            value = value.strip().upper()
            if value not in {"10-K", "10-Q"}: raise ValueError("form must be 10-K or 10-Q")
            return value


class AnswerRequest(EvidenceRequest):
    model_config = {"extra": "forbid"}

    if FastAPI is not None:
        @field_validator("question", mode="before")
        @classmethod
        def reject_control_characters(cls, value):
            if isinstance(value, str) and any(unicodedata.category(char) == "Cc" for char in value):
                raise ValueError("control characters are not allowed")
            return value


def create_app(service: RetrievalService, static_dir=None, answer_service=None):
    if FastAPI is None: raise RuntimeError("FastAPI and Uvicorn are required; install requirements-app.txt")
    app = FastAPI(title="FinSight SEC Evidence", version="0.1.0")

    @app.middleware("http")
    async def request_size_limit(request: Request, call_next):
        limit = 16 * 1024
        declared_size = request.headers.get("content-length")
        if declared_size and declared_size.isdigit() and int(declared_size) > limit:
            return JSONResponse(status_code=413, content={"detail": "request body too large"})
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > limit:
                return JSONResponse(status_code=413, content={"detail": "request body too large"})
        request._body = bytes(body)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _error: RequestValidationError):
        # FastAPI's default 422 response can echo submitted values, including secrets.
        return JSONResponse(status_code=422, content={"detail": "invalid request fields"})

    @app.get("/api/health")
    def health():
        try:
            model_calls = getattr(answer_service, "model_call_count", 0) if answer_service is not None else 0
            return {**service.health(), "ollama_enabled": answer_service is not None,
                "local_model_calls": model_calls, "llm_calls": model_calls}
        except Exception as exc: raise HTTPException(status_code=503, detail="offline retrieval is not ready") from exc

    @app.get("/api/securities")
    def securities(q: Optional[str] = Query(default=None, max_length=100)):
        try: return service.securities(q)
        except Exception as exc: raise HTTPException(status_code=503, detail="offline corpus is not ready") from exc

    def validated_search(request: EvidenceRequest):
        service.load()
        known = {row["symbol"] for row in service.bm25_rows}
        if request.symbol not in known: raise HTTPException(status_code=404, detail="symbol is not covered by the saved corpus")
        cutoff = request.as_of or service.health()["corpus_as_of"]
        if cutoff is not None and parse_time(cutoff, date_only_end=True) > parse_time(service.health()["corpus_as_of"], date_only_end=True):
            raise HTTPException(status_code=400, detail="as_of exceeds corpus cutoff")
        return service.search(query=request.question, symbol=request.symbol, form=request.form,
            as_of=cutoff, top_k=request.top_k)

    @app.post("/api/sec/evidence-search")
    def evidence_search(request: EvidenceRequest):
        try:
            payload = validated_search(request)
            evidence = payload.get("evidence", payload.get("results", []))
            return {**payload, "status": "completed", "answer_status": "not_generated", "evidence": evidence,
                    "results": evidence}
        except HTTPException: raise
        except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail="invalid offline retrieval request") from exc
        except Exception as exc: raise HTTPException(status_code=503, detail="offline retrieval failed") from exc

    @app.post("/api/sec/answer")
    def answer(request: AnswerRequest):
        if answer_service is None:
            return JSONResponse(status_code=503, content={"status": "disabled", "answer_status": "not_generated",
                "detail": "本地模型回答未启用；SEC 证据检索仍可使用。", "external_network_executed": False,
                "local_model_calls": 0, "llm_calls": 0})
        calls_before = getattr(answer_service, "model_call_count", 0)
        def failure(status_code: int, detail: str):
            calls_after = getattr(answer_service, "model_call_count", calls_before)
            attempted = max(0, calls_after - calls_before)
            return JSONResponse(status_code=status_code, content={"status": "failed", "answer_status": "failed",
                "detail": detail, "generation": {"provider": "ollama_local", "local_model_calls": attempted,
                    "llm_calls": attempted, "external_network_executed": False}})
        try:
            payload = validated_search(request)
            return answer_service.generate(question=request.question, retrieval_payload=payload)
        except HTTPException: raise
        except AnswerValidationError:
            return failure(502, "本地模型输出未通过证据校验；SEC 证据检索仍可使用。")
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="invalid offline retrieval request") from exc
        except OllamaModelMissing:
            return failure(503, "所选本地模型尚未安装；SEC 证据检索仍可使用。")
        except OllamaTimeout:
            return failure(504, "本地模型响应超时；SEC 证据检索仍可使用。")
        except OllamaUnavailable:
            return failure(503, "Ollama 本地服务不可用；SEC 证据检索仍可使用。")
        except OllamaError:
            return failure(502, "本地模型响应无效；SEC 证据检索仍可使用。")
        except AnswerGenerationError:
            return failure(503, "本地回答生成失败；SEC 证据检索仍可使用。")
        except Exception:
            return failure(503, "本地回答生成失败；SEC 证据检索仍可使用。")

    if static_dir:
        source = Path(static_dir)
        root = source.resolve()
        if source.is_symlink() or not root.is_dir(): raise ValueError("invalid static directory")
        app.mount("/", StaticFiles(directory=str(root), html=True), name="prototype")
    return app
