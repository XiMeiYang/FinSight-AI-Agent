"""Synthetic-only contracts for the local SEC evidence application."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

from finsight_app.api import create_app
from finsight_app.retrieval_service import RetrievalService


AS_OF = "2026-09-18T23:59:59Z"


class FakeService:
    def __init__(self):
        self.bm25_rows = [{"symbol": "SYN", "company_name": "Synthetic Co", "cik": "0000000001"}]
        self.search_args = None
        self.fail_health = False
        self.fail_search = False

    def load(self):
        return self

    def health(self):
        if self.fail_health:
            raise ValueError("/private/user/SECRET_SENTINEL")
        return {
            "status": "ready", "data_mode": "saved_sec_corpus", "retrieval_mode": "hybrid_rrf",
            "network_executed": False, "llm_calls": 0, "corpus_as_of": AS_OF,
            "document_count": 1, "chunk_count": 1, "supported_symbols": ["SYN"],
            "model_name": "synthetic-fake", "model_revision": "synthetic-1",
        }

    def securities(self, q=None):
        if q and q.lower() not in "syn synthetic co":
            return []
        return [{
            "symbol": "SYN", "company_name": "Synthetic Co", "CIK": "0000000001",
            "available_forms": ["10-K"], "document_count": 1, "chunk_count": 1,
            "corpus_as_of": AS_OF, "rag_available": True,
        }]

    def search(self, **kwargs):
        if self.fail_search:
            raise ValueError("/private/user/SECRET_SENTINEL")
        self.search_args = kwargs
        return {
            **self.health(), "filters": {"symbol": kwargs["symbol"], "form": kwargs["form"], "as_of": kwargs["as_of"]},
            "results": [{
                "rank": 1, "symbol": "SYN", "company_name": "Synthetic Co", "cik": "0000000001",
                "form": "10-K", "accession_number": "0000000001-26-000001",
                "filing_date": "2026-01-01", "section": "Risk Factors", "chunk_id": "synthetic-chunk",
                "source_url": "https://www.sec.gov/Archives/synthetic.htm",
                "evidence_preview": "synthetic evidence",
            }],
        }


@unittest.skipUnless(TestClient is not None, "install requirements-app.txt to run HTTP contracts")
class LocalAppTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeService()
        self.client = TestClient(create_app(self.service))

    def test_health_reports_offline_coverage_without_paths(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["supported_symbols"], ["SYN"])
        self.assertIs(response.json()["network_executed"], False)
        self.assertEqual(response.json()["llm_calls"], 0)
        self.assertNotIn("/private/", response.text)

    def test_securities_are_dynamic_and_searchable(self):
        self.assertEqual(self.client.get("/api/securities?q=synt").json()[0]["symbol"], "SYN")
        self.assertEqual(self.client.get("/api/securities?q=other").json(), [])

    def test_search_returns_evidence_and_point_in_time_filter(self):
        response = self.client.post("/api/sec/evidence-search", json={"symbol": "syn", "question": " What are risks? ", "top_k": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["evidence_preview"], "synthetic evidence")
        self.assertEqual(self.service.search_args, {"query": "What are risks?", "symbol": "SYN", "form": None, "as_of": AS_OF, "top_k": 1})
        self.assertEqual(response.json()["llm_calls"], 0)

    def test_form_and_earlier_cutoff_are_passed_to_hybrid_search(self):
        response = self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "risk", "form": "10-q", "as_of": "2025-01-01", "top_k": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.search_args["form"], "10-Q")
        self.assertEqual(self.service.search_args["as_of"], "2025-01-01")

    def test_unknown_symbol_rejected_before_search(self):
        response = self.client.post("/api/sec/evidence-search", json={"symbol": "NOPE", "question": "risk"})
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(self.service.search_args)

    def test_future_cutoff_rejected_before_search(self):
        response = self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "risk", "as_of": "2027-01-01"})
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.service.search_args)

    def test_invalid_fields_are_sanitized_and_do_not_search(self):
        for payload in (
            {"symbol": "SYN", "question": "   "},
            {"symbol": "SYN", "question": "risk", "form": "8-K"},
            {"symbol": "SYN", "question": "risk", "top_k": 0},
            {"symbol": "SYN", "question": "risk", "top_k": 51},
            {"symbol": "SYN", "question": "/private/user/SECRET_SENTINEL", "top_k": "not-an-int"},
        ):
            with self.subTest(payload=payload):
                response = self.client.post("/api/sec/evidence-search", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("/private/", response.text)
                self.assertNotIn("SECRET_SENTINEL", response.text)
        self.assertIsNone(self.service.search_args)

    def test_internal_errors_are_sanitized(self):
        self.service.fail_health = True
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("/private/", response.text)
        self.service.fail_health = False
        self.service.fail_search = True
        response = self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "risk"})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("/private/", response.text)

    def test_static_page_is_served_from_explicit_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "index.html").write_text("<h1>synthetic page</h1>", encoding="utf-8")
            client = TestClient(create_app(FakeService(), directory))
            self.assertIn("synthetic page", client.get("/").text)
            self.assertEqual(client.get("/api/health").status_code, 200)


class RetrievalServiceTests(unittest.TestCase):
    def test_indexes_and_model_are_loaded_and_validated_once(self):
        embedder = mock.Mock(model_name="synthetic-fake", model_revision="synthetic-1", network_executed=False)
        row = {"symbol": "SYN", "company_name": "Synthetic Co", "cik": "0000000001", "form": "10-K", "document_id": "SYN-1", "corpus_as_of": AS_OF}
        service = RetrievalService(".local_data/bm", ".local_data/dense", ".local_data/corpus", ".local_data/models", "synthetic-1", embedder=embedder)
        with mock.patch("finsight_app.retrieval_service.load_index", return_value=({}, [row], object())) as bm, \
             mock.patch("finsight_app.retrieval_service.load_dense_index", return_value=({}, [row], object())) as dense, \
             mock.patch("finsight_app.retrieval_service.validate_compatible_indexes") as compatible:
            self.assertEqual(service.health()["chunk_count"], 1)
            self.assertEqual(service.health()["document_count"], 1)
            service.securities()
            bm.assert_called_once()
            dense.assert_called_once()
            compatible.assert_called_once()


if __name__ == "__main__":
    unittest.main()
