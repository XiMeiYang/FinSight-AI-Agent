from __future__ import annotations

import os
from pathlib import Path
from threading import Lock

from finsight_rag.dense_retrieval import load_dense_index
from finsight_rag.embeddings import BGEEmbedder
from finsight_rag.hybrid_retrieval import require_offline_environment, search_loaded_hybrid, validate_compatible_indexes
from finsight_rag.retrieval import load_index


class RetrievalService:
    """Loads the verified offline retrieval universe once and serves read-only queries."""

    def __init__(self, bm25_index, dense_index, corpus, model_cache, model_revision,
                 model_name="BAAI/bge-small-en-v1.5", embedder=None):
        self.paths = tuple(Path(x) for x in (bm25_index, dense_index, corpus, model_cache))
        self.model_revision = model_revision
        self.model_name = model_name
        self._embedder = embedder
        self._loaded = False
        self._lock = Lock()

    def load(self):
        if self._loaded:
            return self
        with self._lock:
            if self._loaded:
                return self
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            require_offline_environment()
            if self._embedder is None:
                self._embedder = BGEEmbedder(self.model_name, self.model_revision,
                                             cache_folder=str(self.paths[3]), local_files_only=True)
            self.bm25_manifest, self.bm25_rows, self.bm25 = load_index(self.paths[0], self.paths[2])
            self.dense_manifest, self.dense_rows, self.dense_matrix = load_dense_index(
                self.paths[1], self.paths[2], self._embedder)
            validate_compatible_indexes(self.bm25_manifest, self.bm25_rows,
                self.dense_manifest, self.dense_rows, embedder=self._embedder)
            self._loaded = True
        return self

    @property
    def embedder(self):
        return self._embedder

    def health(self):
        self.load()
        symbols = sorted({row["symbol"] for row in self.bm25_rows})
        as_of = {row.get("corpus_as_of") for row in self.bm25_rows}
        if len(as_of) != 1 or None in as_of:
            raise ValueError("inconsistent corpus cutoff")
        return {"status": "ready", "data_mode": "saved_sec_corpus", "retrieval_mode": "hybrid_rrf",
                "network_executed": False, "llm_calls": 0, "corpus_as_of": next(iter(as_of)),
                "document_count": len({row["document_id"] for row in self.bm25_rows}),
                "chunk_count": len(self.bm25_rows), "supported_symbols": symbols,
                "model_name": self._embedder.model_name, "model_revision": self._embedder.model_revision}

    def securities(self, q=None):
        self.load()
        by_symbol = {}
        for row in self.bm25_rows:
            item = by_symbol.setdefault(row["symbol"], {"symbol": row["symbol"],
                "company_name": row["company_name"], "CIK": row["cik"], "available_forms": set(),
                "document_ids": set(), "chunk_count": 0, "corpus_as_of": row.get("corpus_as_of")})
            item["available_forms"].add(row["form"]); item["document_ids"].add(row["document_id"]); item["chunk_count"] += 1
        if q:
            needle = q.strip().lower()
            by_symbol = {key: value for key, value in by_symbol.items()
                         if needle in key.lower() or needle in value["company_name"].lower()}
        return [{"symbol": x["symbol"], "company_name": x["company_name"], "CIK": x["CIK"],
                 "available_forms": sorted(x["available_forms"]), "document_count": len(x["document_ids"]),
                 "chunk_count": x["chunk_count"], "corpus_as_of": x["corpus_as_of"], "rag_available": True}
                for x in sorted(by_symbol.values(), key=lambda value: value["symbol"])]

    def search(self, **kwargs):
        self.load()
        result = search_loaded_hybrid(self.bm25_manifest, self.bm25_rows, self.bm25,
            self.dense_manifest, self.dense_rows, self.dense_matrix, self._embedder, **kwargs)
        health = self.health()
        return {**result, "data_mode": "saved_sec_corpus", "retrieval_mode": "hybrid_rrf",
                "corpus_as_of": health["corpus_as_of"], "model_name": health["model_name"],
                "model_revision": health["model_revision"]}
