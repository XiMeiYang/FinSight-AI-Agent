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
from finsight_app.ollama_client import OllamaModelMissing, OllamaTimeout, OllamaUnavailable
from finsight_app.retrieval_service import RetrievalService
from finsight_app.research_records import ResearchRecordStore, ResearchRecordCorrupt


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
                "filing_date": "2026-01-01", "section": "Risk Factors", "section_id": "section-1",
                "section_title": "Risk Factors", "chunk_index": 0, "chunk_id": "synthetic-chunk",
                "source_url": "https://www.sec.gov/Archives/synthetic.htm",
                "evidence_preview": "synthetic evidence", "evidence_excerpt": "synthetic evidence",
                "excerpt_truncated": False, "matched_terms": ["risk"], "retrieved_by": "both",
                "bm25_rank": 1, "dense_rank": 2, "rrf_score": 0.03,
            }],
        }


class FakeAnswerService:
    def __init__(self, error=None):
        self.calls = []
        self.error = error
        self.model_call_count = 0

    def generate(self, question, retrieval_payload):
        self.calls.append((question, retrieval_payload))
        if not isinstance(self.error, (OllamaModelMissing, OllamaUnavailable)):
            self.model_call_count += 1
        if self.error:
            raise self.error
        row = retrieval_payload["results"][0]
        return {"answer_status": "completed", "answer": {"answer_status": "completed",
            "direct_answer": {"text": "合成回答", "evidence_ids": ["E1"]},
            "key_points": [{"text": "合成要点", "evidence_ids": ["E1"]}],
            "limitations": ["仅合成测试"]},
            "citations": [{"evidence_id": "E1", "chunk_id": row["chunk_id"], "source_url": row["source_url"]}],
            "evidence": [{"evidence_id": "E1", "evidence_excerpt": row["evidence_excerpt"]}],
            "model_calls": 1, "generation": {"provider": "ollama_local", "model": "synthetic-model",
                "model_digest": "synthetic-digest", "local_model_calls": 1, "llm_calls": 1,
                "external_network_executed": False}}


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

    def test_search_contract_has_not_generated_evidence_and_audit_fields(self):
        payload = self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "risk", "top_k": 10}).json()
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["answer_status"], "not_generated")
        self.assertEqual(payload["retrieval_mode"], "hybrid_rrf")
        self.assertIs(payload["network_executed"], False)
        evidence = payload["evidence"][0]
        for key in ("rank", "chunk_id", "symbol", "company_name", "form", "filing_date",
                    "accession_number", "section_id", "section_title", "chunk_index",
                    "evidence_excerpt", "excerpt_truncated", "matched_terms",
                    "source_url", "retrieved_by", "bm25_rank", "dense_rank", "rrf_score"):
            self.assertIn(key, evidence)

    def test_top_k_eleven_is_rejected_and_ten_is_accepted(self):
        self.assertEqual(self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "risk", "top_k": 10}).status_code, 200)
        self.assertEqual(self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "risk", "top_k": 11}).status_code, 422)

    def test_large_body_is_rejected_without_echoing_input(self):
        response = self.client.post("/api/sec/evidence-search", content=(b"x" * (16 * 1024 + 1)), headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertNotIn("x" * 100, response.text)

    def test_streamed_body_without_declared_length_is_capped(self):
        chunks = iter((b"x" * 8192, b"y" * 8192, b"z"))
        response = self.client.post("/api/sec/evidence-search", content=chunks,
                                    headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json(), {"detail": "request body too large"})

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

    def test_answer_disabled_does_not_call_model_or_break_evidence_search(self):
        self.assertIs(self.client.get("/api/health").json()["ollama_enabled"], False)
        response = self.client.post("/api/sec/answer", json={"symbol": "SYN", "question": "What risks?"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["answer_status"], "not_generated")
        self.assertIsNone(self.service.search_args)
        self.assertEqual(self.client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "What risks?"}).status_code, 200)

    def test_answer_reretrieves_server_evidence_without_accepting_browser_citations(self):
        answer_service = FakeAnswerService()
        client = TestClient(create_app(self.service, answer_service=answer_service))
        self.assertIs(client.get("/api/health").json()["ollama_enabled"], True)
        response = client.post("/api/sec/answer", json={"symbol": "syn", "question": "风险是什么？", "top_k": 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["citations"][0]["chunk_id"], "synthetic-chunk")
        self.assertEqual(self.service.search_args["top_k"], 10)
        self.assertEqual(len(answer_service.calls), 1)
        forbidden = client.post("/api/sec/answer", json={"symbol": "SYN", "question": "What risks?", "evidence": [{"source_url": "https://evil.invalid"}]})
        self.assertEqual(forbidden.status_code, 422)
        self.assertEqual(len(answer_service.calls), 1)

    def test_answer_rejects_control_characters_and_large_body_without_echo(self):
        client = TestClient(create_app(self.service, answer_service=FakeAnswerService()))
        for question in ("abc\ndef", "\tWhat risks?", "a\x00bc"):
            response = client.post("/api/sec/answer", json={"symbol": "SYN", "question": question})
            self.assertEqual(response.status_code, 422)
            self.assertNotIn(question, response.text)
        response = client.post("/api/sec/answer", content=b"x" * (16 * 1024 + 1), headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertIsNone(self.service.search_args)

    def test_answer_model_failures_are_safe_and_evidence_remains_usable(self):
        for error, status in ((OllamaModelMissing("/private/secret"), 503),
                              (OllamaUnavailable("/private/secret"), 503),
                              (OllamaTimeout("/private/secret"), 504)):
            with self.subTest(error=type(error).__name__):
                client = TestClient(create_app(self.service, answer_service=FakeAnswerService(error)))
                response = client.post("/api/sec/answer", json={"symbol": "SYN", "question": "What risks?"})
                self.assertEqual(response.status_code, status)
                self.assertNotIn("/private/", response.text)
                self.assertEqual(response.json()["answer_status"], "failed")
                self.assertIs(response.json()["generation"]["external_network_executed"], False)
                expected_calls = 0 if isinstance(error, (OllamaModelMissing, OllamaUnavailable)) else 1
                self.assertEqual(response.json()["generation"]["llm_calls"], expected_calls)
                self.assertEqual(client.post("/api/sec/evidence-search", json={"symbol": "SYN", "question": "What risks?"}).status_code, 200)

    def test_evidence_insufficient_answer_is_saved_and_history_preserves_status(self):
        class EvidenceInsufficientModel(FakeAnswerService):
            def generate(self, question, retrieval_payload):
                self.calls.append((question, retrieval_payload))
                self.model_call_count += 1
                return {"answer_status": "evidence_insufficient",
                        "answer": {"answer_status": "evidence_insufficient",
                                   "direct_answer": {"text": "证据不足", "evidence_ids": []},
                                   "key_points": [], "limitations": ["证据不足"]},
                        "citations": [], "evidence": [],
                        "generation": {"provider": "ollama_local", "model_digest": "synthetic"}}
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchRecordStore(Path(directory) / "records.sqlite3")
            client = TestClient(create_app(self.service, answer_service=EvidenceInsufficientModel(), research_record_store=store))
            response = client.post("/api/sec/answer", json={"symbol": "SYN", "question": "What risks?"})
            self.assertEqual(response.status_code, 200)
            record_id = response.json()["research_record"]["record_id"]
            history = client.get("/api/research-records/" + record_id)
            self.assertEqual(history.status_code, 200)
            self.assertEqual(history.json()["answer_status"], "evidence_insufficient")
            store.close()

    def test_corrupt_history_list_returns_500(self):
        class CorruptStore:
            def list(self, **_kwargs):
                raise ResearchRecordCorrupt("synthetic corruption")
        response = TestClient(create_app(self.service, research_record_store=CorruptStore())).get("/api/research-records")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "research record is corrupt or incompatible"})

    def test_history_detail_store_failure_returns_503(self):
        class BrokenStore:
            def get(self, _record_id):
                raise RuntimeError("synthetic store failure")
        response = TestClient(create_app(self.service, research_record_store=BrokenStore())).get("/api/research-records/synthetic")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "research records unavailable"})


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

    def test_manifest_replacement_during_load_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bm, dense = root / "bm", root / "dense"
            bm.mkdir(); dense.mkdir()
            (bm / "manifest.json").write_text('{"index_sha256":"old"}')
            (dense / "manifest.json").write_text('{"manifest_sha256":"dense-old"}')
            embedder = mock.Mock(model_name="synthetic-fake", model_revision="synthetic-1")
            row = {"symbol":"SYN", "company_name":"Synthetic Co", "cik":"1", "form":"10-K", "document_id":"SYN-1", "corpus_as_of":AS_OF}
            def replace_bm(*_args):
                (bm / "manifest.json").write_text('{"index_sha256":"replaced"}')
                return ({"index_sha256":"old"}, [row], object())
            service = RetrievalService(bm, dense, root / "corpus", root / "models", "synthetic-1", embedder=embedder)
            with mock.patch("finsight_app.retrieval_service.load_index", side_effect=replace_bm), \
                 mock.patch("finsight_app.retrieval_service.load_dense_index", return_value=({}, [row], object())), \
                 mock.patch("finsight_app.retrieval_service.validate_compatible_indexes"):
                with self.assertRaisesRegex(ValueError, "manifest changed"):
                    service.load()

    def test_loaded_snapshot_fingerprint_survives_later_manifest_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bm, dense = root / "bm", root / "dense"
            bm.mkdir(); dense.mkdir()
            (bm / "manifest.json").write_text('{"index_sha256":"old"}')
            (dense / "manifest.json").write_text('{"manifest_sha256":"dense-old"}')
            embedder = mock.Mock(model_name="synthetic-fake", model_revision="synthetic-1")
            row = {"symbol":"SYN", "company_name":"Synthetic Co", "cik":"1", "form":"10-K", "document_id":"SYN-1", "corpus_as_of":AS_OF}
            service = RetrievalService(bm, dense, root / "corpus", root / "models", "synthetic-1", embedder=embedder)
            with mock.patch("finsight_app.retrieval_service.load_index", return_value=({"index_sha256":"old"}, [row], object())), \
                 mock.patch("finsight_app.retrieval_service.load_dense_index", return_value=({"manifest_sha256":"dense-old"}, [row], object())), \
                 mock.patch("finsight_app.retrieval_service.validate_compatible_indexes"):
                service.load()
            old = dict(service.corpus_fingerprint)
            (bm / "manifest.json").write_text('{"index_sha256":"new"}')
            self.assertEqual(service.corpus_fingerprint, old)

    def test_answer_history_uses_loaded_old_manifest_bytes_after_disk_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bm, dense = root / "bm", root / "dense"
            bm.mkdir(); dense.mkdir()
            (bm / "manifest.json").write_text('{"index_sha256":"old"}')
            (dense / "manifest.json").write_text('{"manifest_sha256":"dense-old"}')
            embedder = mock.Mock(model_name="synthetic-fake", model_revision="synthetic-1")
            row = {"symbol":"SYN", "company_name":"Synthetic Co", "cik":"1", "form":"10-K", "document_id":"SYN-1", "corpus_as_of":AS_OF}
            service = RetrievalService(bm, dense, root / "corpus", root / "models", "synthetic-1", embedder=embedder)
            with mock.patch("finsight_app.retrieval_service.load_index", return_value=({"index_sha256":"old"}, [row], object())), \
                 mock.patch("finsight_app.retrieval_service.load_dense_index", return_value=({"manifest_sha256":"dense-old"}, [row], object())), \
                 mock.patch("finsight_app.retrieval_service.validate_compatible_indexes"):
                service.load()
                old = dict(service.corpus_fingerprint)
                (bm / "manifest.json").write_text('{"index_sha256":"new"}')
                with tempfile.TemporaryDirectory() as records_dir:
                    store = ResearchRecordStore(Path(records_dir) / "records.sqlite3")
                    service.search = mock.Mock(return_value={**service.health(), "filters": {"as_of": AS_OF}, "results": [{"symbol":"SYN", "chunk_id":"c1", "source_url":"https://sec.invalid/synthetic", "evidence_excerpt":"synthetic"}]})
                    client = TestClient(create_app(service, answer_service=FakeAnswerService(), research_record_store=store))
                    response = client.post("/api/sec/answer", json={"symbol":"SYN", "question":"risk"})
                    self.assertEqual(response.status_code, 200)
                    rid = response.json()["research_record"]["record_id"]
                    detail = client.get("/api/research-records/" + rid).json()
                    self.assertEqual(detail["model_metadata"]["corpus_fingerprint"], old)
                    store.close()


if __name__ == "__main__":
    unittest.main()
