import json, unittest
import subprocess, sys
from pathlib import Path
from finsight_research import build_research_snapshot, SnapshotError, SnapshotConflictError
from finsight_research.models import ResearchSnapshot

ROOT=Path(__file__).parents[1]; F=ROOT/"tests/fixtures"
class TestSnapshot(unittest.TestCase):
    def setUp(self):
        av=json.loads((F/"alpha_vantage_daily.synthetic.json").read_text()); facts=json.loads((F/"sec_companyfacts.synthetic.json").read_text()); filings=json.loads((F/"sec_submissions.synthetic.json").read_text())
        rows=[]
        for d,v in av["Time Series (Daily)"].items(): rows.append({"as_of":d,"timestamp":d+"T00:00:00Z","open":float(v["1. open"]),"high":float(v["2. high"]),"low":float(v["3. low"]),"close":float(v["4. close"]),"volume":int(v["5. volume"])})
        self.kw=dict(symbol="test",market_data={"source":"alpha_vantage","source_url":"u","retrieved_at":"2024-01-04T00:00:00Z","rows":rows,"raw_sha256":"abc"},company_facts=facts,filings=filings,as_of="2024-12-31",data_mode="synthetic",clock=lambda:"2024-01-05T00:00:00Z",snapshot_id="s",run_id="r")
    def test_complete_and_deterministic(self):
        x=build_research_snapshot(**self.kw); self.assertEqual(x["data_mode"],"synthetic"); self.assertFalse(x["run_record"]["network_executed"]); self.assertEqual(x["run_record"]["model_calls"],0); self.assertEqual(len(x["market_data"]["bars"]),2); self.assertEqual(x["market_data"]["latest_bar"]["as_of"],"2024-01-03"); self.assertEqual(len(x["sec_filings"]),1); self.assertEqual(len(x["sec_facts"]),1); self.assertEqual(x["sources"][0]["raw_sha256"],"abc")
    def test_pit_and_missing(self):
        x=build_research_snapshot(**{**self.kw,"as_of":"2023-01-01"}); self.assertEqual(x["data_quality"]["status"],"failed"); self.assertGreater(x["data_quality"]["point_in_time_filtered_count"],0)
    def test_invalid(self):
        with self.assertRaises(SnapshotError): build_research_snapshot(**{**self.kw,"symbol":"bad symbol"})
        with self.assertRaises(SnapshotError): build_research_snapshot(**{**self.kw,"as_of":"bad"})
    def test_input_unchanged(self):
        before=json.dumps(self.kw["market_data"],sort_keys=True); build_research_snapshot(**self.kw); self.assertEqual(before,json.dumps(self.kw["market_data"],sort_keys=True))
    def test_schema_and_run_contract(self):
        x=build_research_snapshot(**self.kw); self.assertEqual(x["schema_version"],"1.0"); self.assertEqual(x["snapshot_type"],"single_stock_research"); self.assertEqual(x["run_record"]["model_calls"],0); self.assertFalse(x["run_record"]["network_executed"])
    def test_filing_location_and_source(self):
        x=build_research_snapshot(**self.kw); self.assertIn("000000000024000001",x["sec_filings"][0]["filing_url"]); self.assertEqual(x["sec_filings"][0]["accession_number"],"0000000000-24-000001"); self.assertEqual(len(x["sources"]),2)
    def test_market_cutoff(self):
        x=build_research_snapshot(**{**self.kw,"as_of":"2024-01-02"}); self.assertEqual(len(x["market_data"]["bars"]),1); self.assertEqual(x["market_data"]["latest_bar"]["as_of"],"2024-01-02")
    def test_missing_data_partial(self):
        x=build_research_snapshot(**{**self.kw,"market_data":None}); self.assertEqual(x["data_quality"]["status"],"partial"); self.assertIn("market_data",x["data_quality"]["missing_fields"])
        x=build_research_snapshot(**{**self.kw,"company_facts":None,"filings":None}); self.assertEqual(x["data_quality"]["status"],"partial")
    def test_all_missing_failed(self):
        x=build_research_snapshot(symbol="TEST",market_data=None,company_facts=None,filings=None,as_of="2024-01-01",data_mode="synthetic",clock=lambda:"2024-01-02T00:00:00Z"); self.assertEqual(x["data_quality"]["status"],"failed")
    def test_missing_available_at_filtered(self):
        facts={"rows":[{"tag":"X","value":1,"unit":"USD","available_at":None}]}; x=build_research_snapshot(**{**self.kw,"company_facts":facts}); self.assertEqual(x["sec_facts"],[])
    def test_unknown_hash_is_null(self):
        x=build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"raw_sha256":None}}); self.assertIsNone(x["sources"][0]["raw_sha256"])
    def test_saved_snapshot_mode(self):
        self.assertEqual(build_research_snapshot(**{**self.kw,"data_mode":"saved_snapshot"})["data_mode"],"saved_snapshot")
    def test_bad_mode(self):
        with self.assertRaises(SnapshotError): build_research_snapshot(**{**self.kw,"data_mode":"live"})
    def test_full_datetime_cutoff(self):
        market={**self.kw["market_data"],"rows":[{"as_of":"2024-01-02","timestamp":"2024-01-02T12:00:00Z","close":1}]}
        x=build_research_snapshot(**{**self.kw,"market_data":market,"as_of":"2024-01-02T11:00:00Z"}); self.assertEqual(x["market_data"]["bars"],[])
    def test_cli_rejects_real_symbol_in_fixture(self):
        p=subprocess.run([sys.executable,"scripts/build_research_snapshot.py","NVDA","--fixture","--as-of","2024-12-31"],cwd=ROOT,env={**__import__('os').environ,"PYTHONPATH":"src"},capture_output=True,text=True); self.assertNotEqual(p.returncode,0); self.assertIn("only accepts TEST",p.stderr)
    def test_missing_market_date_is_skipped(self):
        market={**self.kw["market_data"],"rows":[{"close":1},*self.kw["market_data"]["rows"]]}; x=build_research_snapshot(**{**self.kw,"market_data":market}); self.assertEqual(len(x["market_data"]["bars"]),2)
    def test_all_missing_has_no_sources_and_failed_run(self):
        x=build_research_snapshot(symbol="TEST",market_data=None,company_facts=None,filings=None,as_of="2024-01-01",data_mode="synthetic",clock=lambda:"2024-01-02T00:00:00Z"); self.assertEqual(x["sources"],[]); self.assertEqual(x["run_record"]["status"],"failed")
    def test_symbol_conflict_rejected(self):
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"symbol":"NVDA"}})
    def test_cik_conflict_rejected(self):
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"cik":"1"},"company_facts":{**self.kw["company_facts"],"cik":"2"}})
    def test_bar_symbol_conflict(self):
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"rows":[{"symbol":"NVDA","as_of":"2024-01-02"}]}})
    def test_filing_cik_conflict(self):
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"filings":[{"cik":"999","filing_date":"2024-01-01","form":"10-K"}]})
    def test_invalid_and_padded_cik(self):
        x=build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"cik":"123"},"company_facts":{**self.kw["company_facts"],"cik":"123"},"filings":[]}); self.assertEqual(x["security"]["cik"],"0000000123")
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"cik":"bad"}})
    def test_weak_company_alias_conflict(self):
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"company_name":"Market Corp"},"company_facts":{**self.kw["company_facts"],"entityName":"Facts Corp"}})
    def test_company_name_alias_conflict(self):
        with self.assertRaises(SnapshotConflictError): build_research_snapshot(**{**self.kw,"company_facts":{**self.kw["company_facts"],"company_name":"Other Corp"}})
    def test_facts_only_weak_fields_are_merged(self):
        x=build_research_snapshot(**{**self.kw,"company_facts":{**self.kw["company_facts"],"exchange":"NASDAQ","currency":"USD"}}); self.assertEqual(x["security"]["exchange"],"NASDAQ"); self.assertEqual(x["security"]["currency"],"USD")
        self.assertNotIn("currency unavailable", x["data_quality"]["warnings"])
    def test_facts_only_company_name_is_merged(self):
        facts={**self.kw["company_facts"],"company_name":"Facts Corp"}; facts.pop("entityName",None); x=build_research_snapshot(**{**self.kw,"market_data":{**self.kw["market_data"],"company_name":None},"company_facts":facts}); self.assertEqual(x["security"]["company_name"],"Facts Corp")
    def test_snapshot_is_dict_contract(self):
        x=build_research_snapshot(**self.kw); self.assertIsInstance(x,dict); self.assertIn("security",x); self.assertTrue(hasattr(ResearchSnapshot,"__annotations__"))
if __name__=='__main__': unittest.main()
