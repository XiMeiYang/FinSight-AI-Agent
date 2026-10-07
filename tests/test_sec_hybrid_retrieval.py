import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
import numpy as np
from unittest import mock

from finsight_rag.bm25 import BM25Index
from finsight_rag.embeddings import FakeEmbedder
from finsight_rag.hybrid_retrieval import RRF_DEPTH,RRF_K,RRF_WEIGHTS,enrich_results,evaluate_three_way,fuse_results,require_offline_environment,search_loaded_hybrid,validate_compatible_indexes,validate_query_file
from finsight_rag.retrieval import TOKENIZER_VERSION


def item(chunk, rank, score=1.0, symbol="AAA"):
    return {"chunk_id": chunk, "rank": rank, "score": score, "symbol": symbol,
            "accession_number": "0000000001-24-000001", "section": "Risk",
            "chunk_index": 0, "evidence_preview": "synthetic"}


class HybridTests(unittest.TestCase):
    def test_constants(self): self.assertEqual((RRF_K,RRF_DEPTH,RRF_WEIGHTS),(60,50,{"bm25":1,"dense":1}))
    def test_fixed_rrf_and_original_scores_are_audit_only(self):
        out = fuse_results([item("a", 1, 0.01), item("b", 2, 999)], [item("b", 1, 0.02), item("c", 2, 999)], top_k=3)
        self.assertEqual([x["chunk_id"] for x in out], ["b", "a", "c"])
        self.assertAlmostEqual(out[0]["rrf_score"], 1/61 + 1/62)
        self.assertEqual(out[0]["source_composition"], "both")
        self.assertEqual(out[1]["source_composition"], "bm25")
        self.assertEqual(out[2]["source_composition"], "dense")
        self.assertEqual(out[0]["bm25_score"], 999); self.assertEqual(out[0]["dense_score"], 0.02)

    def test_depth_topk_and_tie_break_are_deterministic(self):
        left = [item(f"x{i}", i) for i in range(1, 61)]
        right = [item(f"y{i}", i) for i in range(1, 61)]
        self.assertEqual(len(fuse_results(left, right, top_k=50)), 50)
        self.assertEqual([x["chunk_id"] for x in fuse_results(left, right, top_k=50)], [x["chunk_id"] for x in fuse_results(left, right, top_k=50)])
        with self.assertRaises(ValueError): fuse_results(left, right, top_k=0)
        with self.assertRaises(ValueError): fuse_results(left, right, rrf_k=10)

    def test_compatible_indexes_require_same_universe_and_offline(self):
        rows = [{"chunk_id":"a", "text":"same", "corpus_as_of":"2026"}]
        manifest = {"corpus_aggregate_sha256":"c", "corpus_chunks_sha256":"d", "indexed_documents_sha256":"i", "tokenizer_version":TOKENIZER_VERSION, "network_executed":False}
        dense = dict(manifest, model_name="model", model_revision="rev", network_executed=False)
        validate_compatible_indexes(manifest, rows, dense, rows)
        with self.assertRaises(ValueError): validate_compatible_indexes(manifest, rows, dense, [{"chunk_id":"b", "text":"same", "corpus_as_of":"2026"}])
        with self.assertRaises(ValueError): validate_compatible_indexes(manifest, rows, dict(dense, network_executed=True), rows)

    def test_missing_chunk_id_and_preview_are_rejected_or_bounded(self):
        with self.assertRaises(ValueError): fuse_results([{"score":1}], [])
        result = fuse_results([{**item("a", 1), "evidence_preview":"x"*1000}], [], top_k=1)
        self.assertLessEqual(len(result[0]["evidence_preview"]), 400)

    def test_single_source_has_null_other_audit_fields(self):
        row=fuse_results([item("a",1)],[],top_k=1)[0]
        self.assertEqual(row["retrieved_by"],"bm25"); self.assertIsNone(row["dense_rank"]); self.assertIsNone(row["dense_score"])

    def test_conflicting_identity_rejected(self):
        with self.assertRaises(ValueError): fuse_results([item("a",1,symbol="AAA")],[item("a",1,symbol="BBB")])

    def test_same_source_duplicate_rejected(self):
        with self.assertRaises(ValueError): fuse_results([item("a",1),item("a",2)],[])

    def test_result_fields_and_depth(self):
        row=fuse_results([item("a",1)],[],top_k=1)[0]
        self.assertEqual(row["rrf_depth"],50); self.assertEqual(row["rrf_k"],60); self.assertIn("section_id",row)

    def test_raw_score_does_not_change_order(self):
        a=[item("a",1,0.0),item("b",2,100000)]
        self.assertEqual([x["chunk_id"] for x in fuse_results(a,[],top_k=2)], ["a","b"])

    def test_tie_break_both_before_single(self):
        out=fuse_results([item("a",1),item("b",2)],[item("b",1)],top_k=2)
        self.assertEqual(out[0]["retrieved_by"],"both")

    def test_offline_argument_rejected(self):
        rows=[{"chunk_id":"a","text":"same","corpus_as_of":"2026"}]; m={"corpus_aggregate_sha256":"c","corpus_chunks_sha256":"d","indexed_documents_sha256":"i","tokenizer_version":TOKENIZER_VERSION,"network_executed":False}; d=dict(m,model_name="m",model_revision="r")
        with self.assertRaises(ValueError): validate_compatible_indexes(m,rows,d,rows,offline=False)

    def test_text_conflict_rejected(self):
        rows=[{"chunk_id":"a","text":"x","corpus_as_of":"2026"}]; other=[{"chunk_id":"a","text":"y","corpus_as_of":"2026"}]; m={"corpus_aggregate_sha256":"c","corpus_chunks_sha256":"d","indexed_documents_sha256":"i","tokenizer_version":TOKENIZER_VERSION,"network_executed":False}; d=dict(m,model_name="m",model_revision="r")
        with self.assertRaises(ValueError): validate_compatible_indexes(m,rows,d,other)

    def test_provenance_conflict_rejected(self):
        rows=[{"chunk_id":"a","text":"x","corpus_as_of":"2026"}]; m={"corpus_aggregate_sha256":"c","corpus_chunks_sha256":"d","indexed_documents_sha256":"i","tokenizer_version":TOKENIZER_VERSION,"network_executed":False}; d=dict(m,corpus_aggregate_sha256="z",model_name="m",model_revision="r")
        with self.assertRaises(ValueError): validate_compatible_indexes(m,rows,d,rows)

    def test_form_and_symbol_identity_visible(self):
        row=fuse_results([item("a",1)],[],top_k=1)[0]; self.assertEqual(row["symbol"],"AAA"); self.assertIsNone(row.get("form"))

    def test_top_k_limit(self):
        with self.assertRaises(ValueError): fuse_results([],[],top_k=51)

    def test_preview_limit(self):
        self.assertEqual(len(fuse_results([{**item("a",1),"evidence_preview":"x"*999}],[],top_k=1)[0]["evidence_preview"]),400)

    def test_score_null_for_missing_source(self):
        self.assertIsNone(fuse_results([], [item("a",1)],top_k=1)[0]["bm25_score"])

    def test_retrieved_by_stable(self):
        self.assertEqual(fuse_results([item("a",1)],[item("a",1)],top_k=1)[0]["retrieved_by"],"both")

    def test_enrich_adds_index_identity_and_rejects_text_mismatch(self):
        row={**item("a",1),"company_name":None,"cik":None,"form":None,"document_id":"doc","filing_date":None,"accepted_at":None,"published_at":None,"section_id":"risk","source_url":None,"corpus_as_of":None,"text":"synthetic body"}
        result={**item("a",1),"evidence_preview":"synthetic body"}
        self.assertEqual(enrich_results([result],[row])[0]["document_id"],"doc")
        with self.assertRaises(ValueError):enrich_results([{**result,"evidence_preview":"other"}],[row])

    def test_model_revision_and_tokenizer_conflicts(self):
        rows=[{"chunk_id":"a","text":"same","corpus_as_of":"2026"}];m={"corpus_aggregate_sha256":"c","corpus_chunks_sha256":"d","indexed_documents_sha256":"i","tokenizer_version":TOKENIZER_VERSION,"network_executed":False};d=dict(m,model_name="m",model_revision="r")
        embedder=type("E",(),{"model_name":"m","model_revision":"wrong","network_executed":False})()
        with self.assertRaises(ValueError):validate_compatible_indexes(m,rows,d,rows,embedder=embedder)
        with self.assertRaises(ValueError):validate_compatible_indexes(dict(m,tokenizer_version="bad"),rows,d,rows)

    def test_three_way_metrics_filters_recovery_and_failures(self):
        query_rows=[{"query_id":f"q{i}","query":f"query{i}","filters":{"symbol":"AAA","form":"10-K","as_of":"2026-01-01"},"expected_chunk_ids":[expected]} for i,expected in enumerate(("a","b","c","z"),1)]
        calls=[]
        def search(source):
            def run(query,filters,depth):
                calls.append((source,query,dict(filters),depth));mapping={"query1":[item("a",1)],"query2":[item("b",1)] if source=="bm25" else [item("x",1)],"query3":[item("c",1)] if source=="dense" else [item("y",1)],"query4":[]};return mapping[query]
            return run
        provenance={"queries_sha256":"q","corpus_aggregate_sha256":"c","bm25_index_sha256":"b","dense_documents_sha256":"d","dense_embeddings_sha256":"e","model_name":"m","model_revision":"r"}
        with mock.patch("socket.create_connection",side_effect=AssertionError("network attempted")):
            result=evaluate_three_way(query_rows,search("bm25"),search("dense"),lambda row:"business",provenance=provenance)
        self.assertEqual(result["hybrid_vs_bm25"],{"improved":1,"tie":3,"declined":0})
        self.assertEqual(result["hybrid_vs_dense"],{"improved":1,"tie":3,"declined":0})
        self.assertEqual(result["bm25_only_preserved_count"],1);self.assertEqual(result["dense_only_recovered_count"],1)
        self.assertEqual(result["three_way_success"],{"all_three_success":1,"only_hybrid_success":0,"hybrid_failed":1,"all_three_failed":1})
        self.assertEqual(result["metrics"]["hybrid"]["no_result_rate"],.25)
        self.assertEqual(len(calls),8);self.assertTrue(all(call[2]==query_rows[0]["filters"] and call[3]==50 for call in calls))
        self.assertEqual(len(result["query_details"]),4);self.assertEqual(result["query_details"][3]["expected_chunk_ids"],["z"])
        self.assertEqual(result["provenance"],provenance)

    def test_first_tie_break_uses_symbol_then_accession(self):
        left=[item("z",1,symbol="BBB"),item("a",2,symbol="AAA")]
        right=[item("a",1,symbol="AAA"),item("z",2,symbol="BBB")]
        self.assertEqual([row["chunk_id"] for row in fuse_results(left,right,top_k=2)],["a","z"])

    def test_hybrid_search_input_filters_pit_and_private_output(self):
        row={"chunk_id":"a","document_id":"doc","symbol":"AAA","company_name":"Alpha Synthetic","cik":"0000000001","form":"10-K","accession_number":"0000000001-24-000001","filing_date":"2024-01-01","accepted_at":"2024-01-01T12:00:00Z","published_at":"2024-01-01","section_id":"risk","section_title":"Risk","chunk_index":0,"source_url":"https://www.sec.gov/Archives/test.htm","corpus_as_of":"2026-01-01T00:00:00Z","text":"alpha risk"}
        base={"corpus_aggregate_sha256":"c","corpus_chunks_sha256":"d","indexed_documents_sha256":"i","network_executed":False};bm_manifest={**base,"tokenizer_version":TOKENIZER_VERSION};embedder=FakeEmbedder(8);dense_manifest={**base,"model_name":embedder.model_name,"model_revision":embedder.model_revision,"dimension":8,"normalization":True}
        bm25=BM25Index([["alpha","risk"]]);matrix=embedder.encode_documents([row["text"]])
        result=search_loaded_hybrid(bm_manifest,[row],bm25,dense_manifest,[row],matrix,embedder,"alpha",symbol="AAA",form="10-K",as_of="2025-01-01")
        rendered=json.dumps(result);self.assertTrue(result["results"]);self.assertNotIn("/Users/",rendered);self.assertNotIn("@",rendered);self.assertNotIn("FINSIGHT_SEC_USER_AGENT",rendered)
        self.assertEqual(search_loaded_hybrid(bm_manifest,[row],bm25,dense_manifest,[row],matrix,embedder,"alpha",as_of="2023-01-01")["results"],[])
        for query,kwargs in (("",{}),("x"*2001,{}),("alpha",{"top_k":0}),("alpha",{"symbol":"ZZZ"}),("alpha",{"form":"8-K"}),("alpha",{"as_of":"bad"})):
            with self.assertRaises(ValueError):search_loaded_hybrid(bm_manifest,[row],bm25,dense_manifest,[row],matrix,embedder,query,**kwargs)

    def test_frozen_query_sha_fails_before_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root=__import__('pathlib').Path(directory)/'.local_data';root.mkdir();path=root/'queries.json';path.write_bytes(b'original');expected=hashlib.sha256(b'original').hexdigest();self.assertEqual(validate_query_file(path,expected),expected)
            path.write_bytes(b'changed');calls=[]
            with self.assertRaises(ValueError):validate_query_file(path,expected)
            self.assertEqual(calls,[])

    def test_offline_environment_and_both_clis_fail_closed(self):
        valid={"HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","HF_HUB_DISABLE_TELEMETRY":"1"};require_offline_environment(valid)
        for key in valid:
            bad=dict(valid);bad.pop(key)
            with self.assertRaises(ValueError):require_offline_environment(bad)
        arguments=['--bm25-index','x','--dense-index','x','--corpus','x','--model-revision','x','--offline']
        environment={key:value for key,value in os.environ.items() if key not in valid};environment['PYTHONPATH']='src'
        for script,extra in [('scripts/search_sec_hybrid.py',['--query','x']),('scripts/evaluate_sec_hybrid_comparison.py',['--queries','x','--output','.local_data/x.json'])]:
            completed=subprocess.run([sys.executable,script,*arguments,*extra],cwd='.',env=environment,capture_output=True,text=True)
            self.assertNotEqual(completed.returncode,0);self.assertIn('HF_HUB_OFFLINE=1 is required',completed.stderr)


if __name__ == "__main__": unittest.main()
