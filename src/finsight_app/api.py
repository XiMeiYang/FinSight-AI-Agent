from __future__ import annotations

from pathlib import Path
from typing import Optional

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


class EvidenceRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)
    question: str = Field(min_length=1, max_length=2000)
    form: Optional[str] = None
    as_of: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=50)

    if FastAPI is not None:
        @field_validator("symbol")
        def normalize_symbol(cls, value): return value.strip().upper()

        @field_validator("question")
        def non_blank_question(cls, value):
            if not value.strip(): raise ValueError("question must not be blank")
            return value.strip()

        @field_validator("form")
        def normalize_form(cls, value):
            if value is None: return value
            value = value.strip().upper()
            if value not in {"10-K", "10-Q"}: raise ValueError("form must be 10-K or 10-Q")
            return value


def create_app(service: RetrievalService, static_dir=None):
    if FastAPI is None: raise RuntimeError("FastAPI and Uvicorn are required; install requirements-app.txt")
    app = FastAPI(title="FinSight SEC Evidence", version="0.1.0")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _error: RequestValidationError):
        # FastAPI's default 422 response can echo submitted values, including secrets.
        return JSONResponse(status_code=422, content={"detail": "invalid request fields"})

    @app.get("/api/health")
    def health():
        try: return service.health()
        except Exception as exc: raise HTTPException(status_code=503, detail="offline retrieval is not ready") from exc

    @app.get("/api/securities")
    def securities(q: Optional[str] = Query(default=None, max_length=100)):
        try: return service.securities(q)
        except Exception as exc: raise HTTPException(status_code=503, detail="offline corpus is not ready") from exc

    @app.post("/api/sec/evidence-search")
    def evidence_search(request: EvidenceRequest):
        try:
            service.load()
            known = {row["symbol"] for row in service.bm25_rows}
            if request.symbol not in known: raise HTTPException(status_code=404, detail="symbol is not covered by the saved corpus")
            cutoff = request.as_of or service.health()["corpus_as_of"]
            if cutoff is not None and parse_time(cutoff, date_only_end=True) > parse_time(service.health()["corpus_as_of"], date_only_end=True):
                raise HTTPException(status_code=400, detail="as_of exceeds corpus cutoff")
            return service.search(query=request.question, symbol=request.symbol, form=request.form,
                as_of=cutoff, top_k=request.top_k)
        except HTTPException: raise
        except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail="invalid offline retrieval request") from exc
        except Exception as exc: raise HTTPException(status_code=503, detail="offline retrieval failed") from exc

    if static_dir:
        source = Path(static_dir)
        root = source.resolve()
        if source.is_symlink() or not root.is_dir(): raise ValueError("invalid static directory")
        app.mount("/", StaticFiles(directory=str(root), html=True), name="prototype")
    return app
