"""Build deterministic, offline ResearchSnapshot objects."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib, re
from typing import Optional

class SnapshotError(ValueError): pass
class SnapshotConflictError(SnapshotError): pass
_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")
_CIK = re.compile(r"^\d{1,10}$")

def _iso(value):
    if not isinstance(value, str): raise SnapshotError("as_of must be ISO date or datetime")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if "T" not in value: dt = dt.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError as exc: raise SnapshotError("invalid as_of") from exc

def _day(value): return str(value)[:10] if value else None
def _before(value, cutoff):
    if not value: return False
    text=str(value).replace("Z", "+00:00")
    try:
        if text.isdigit() and len(text) == 14:
            # SEC acceptanceDateTime is a local Eastern time value without an
            # offset.  ZoneInfo applies EST/EDT correctly at DST boundaries.
            dt=datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("America/New_York"))
            return dt <= datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
        if "T" not in text: text += "T23:59:59+00:00"
        dt=datetime.fromisoformat(text)
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt <= datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    except ValueError: return False
def _id(prefix, symbol, as_of): return prefix + "-" + hashlib.sha256(f"{symbol}|{as_of}".encode()).hexdigest()[:16]

def _validate_ticker_mapping(mapping, symbol):
    if not mapping:
        return None, None
    if isinstance(mapping, list): rows = mapping
    elif isinstance(mapping, dict) and not any(k in mapping for k in ("ticker", "symbol", "cik", "cik_str")): rows = list(mapping.values())
    else: rows = [mapping]
    rows = [row for row in rows if isinstance(row, dict)]
    matches = [row for row in rows if str(row.get("ticker", row.get("symbol", ""))).strip().upper() == symbol]
    if len(matches) != 1: raise SnapshotConflictError("ticker mapping must contain exactly one requested ticker")
    row = matches[0]; ticker = str(row.get("ticker", row.get("symbol", ""))).strip().upper()
    cik = row.get("cik", row.get("cik_str"))
    if not ticker or not cik: raise SnapshotConflictError("ticker mapping ticker and CIK are required")
    if not _CIK.fullmatch(str(cik)) or int(str(cik)) == 0: raise SnapshotConflictError("ticker mapping CIK must be a non-zero decimal")
    return row, str(cik)

def build_research_snapshot(*, symbol, market_data=None, company_facts=None, filings=None,
                            ticker_mapping=None, as_of, data_mode, clock=None,
                            snapshot_id=None, run_id=None, target_forms=("10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A")):
    if not isinstance(symbol, str): raise SnapshotError("symbol must be text")
    symbol = symbol.strip().upper()
    if not _SYMBOL.fullmatch(symbol): raise SnapshotError("invalid symbol")
    if data_mode not in {"synthetic", "saved_snapshot"}: raise SnapshotError("data_mode must be synthetic or saved_snapshot")
    cutoff = _iso(as_of); cutoff_day = cutoff[:10]
    now = _iso((clock or (lambda: datetime.now(timezone.utc).isoformat()))())
    market = deepcopy(market_data or {}); facts_payload = deepcopy(company_facts or {}); filing_input = deepcopy(filings or {})
    mapping = deepcopy(ticker_mapping or {})
    allowed_forms = {str(form).strip().upper() for form in target_forms}
    if not allowed_forms: raise SnapshotError("target_forms must not be empty")
    conflicts=[]; warnings=[]
    filter_counts={"non_target_form":0,"market_after_as_of":0,"market_missing_timestamp":0,"filing_after_as_of":0,"fact_after_as_of":0,"missing_fact_available_at":0,"filing_availability_unknown":0}
    weak_values={"company_name":(market.get("company_name"),facts_payload.get("company_name"),facts_payload.get("entity_name"),facts_payload.get("entityName")),"exchange":(market.get("exchange"),facts_payload.get("exchange")),"currency":(market.get("currency"),facts_payload.get("currency"))}
    for field, candidates in weak_values.items():
        vals={str(v).strip() for v in candidates if v not in (None, "")}
        if len(vals)>1: conflicts.append(f"{field} conflict")
    if conflicts: raise SnapshotConflictError("weak field conflict: " + ", ".join(conflicts))
    cik_values=[v for v in (market.get("cik"), facts_payload.get("cik")) if v is not None]
    for cik in cik_values:
        if not _CIK.fullmatch(str(cik)): raise SnapshotConflictError("invalid CIK")
    supplied_symbols={str(market.get("symbol", "")).strip().upper(), str(facts_payload.get("symbol", "")).strip().upper()}
    supplied_symbols.discard("")
    if supplied_symbols and supplied_symbols != {symbol}: raise SnapshotConflictError("symbol conflict in snapshot inputs")
    market_cik=market.get("cik"); facts_cik=facts_payload.get("cik")
    if market_cik and facts_cik and str(market_cik).zfill(10) != str(facts_cik).zfill(10): raise SnapshotConflictError("CIK conflict in snapshot inputs")
    mapping, mapping_cik = _validate_ticker_mapping(mapping, symbol)
    all_ciks = [v for v in (market_cik, facts_cik, mapping_cik) if v is not None]
    if all_ciks and len({str(v).zfill(10) for v in all_ciks}) > 1: raise SnapshotConflictError("ticker mapping CIK conflict")
    if not (market.get("currency") or facts_payload.get("currency")): warnings.append("currency unavailable")
    raw_cik=market.get("cik") or facts_payload.get("cik")
    raw_cik = raw_cik or mapping_cik
    security = {"symbol": symbol, "company_name": market.get("company_name") or facts_payload.get("company_name") or facts_payload.get("entity_name") or facts_payload.get("entityName"), "cik": str(raw_cik).zfill(10) if raw_cik is not None else None, "exchange": market.get("exchange") or facts_payload.get("exchange"), "currency": market.get("currency") or facts_payload.get("currency")}
    if mapping:
        security["ticker_mapping"] = {k: mapping[k] for k in ("ticker", "symbol", "cik", "cik_str", "source_url", "retrieved_at", "raw_sha256", "normalized_sha256", "input_file") if k in mapping}
    market_rows=market.get("rows", market.get("bars", [])); bars=[]
    excluded_count = 0
    for row in market_rows:
        marker = row.get("timestamp") or row.get("as_of") or row.get("date")
        if not marker:
            excluded_count += 1; filter_counts["market_missing_timestamp"] += 1
        elif _before(marker, cutoff): bars.append(deepcopy(row))
        else: excluded_count += 1; filter_counts["market_after_as_of"]+=1
    bars.sort(key=lambda row: (row.get("as_of") or row.get("date") or row.get("timestamp"), repr(sorted(row.items()))))
    for row in bars:
        if row.get("symbol") and str(row["symbol"]).strip().upper() != symbol: raise SnapshotConflictError("bar symbol conflict")
        row.setdefault("symbol", symbol)
    latest = bars[-1] if bars else None
    market_out = {"source": market.get("source"), "source_url": market.get("source_url"), "retrieved_at": market.get("retrieved_at"), "data_as_of": latest.get("as_of") if latest else None, "currency": market.get("currency"), "adjustment": market.get("adjustment"), "bars": bars, "latest_bar": latest, "missing_reason": None if bars else "no market data available by as_of"}
    recent = filing_input.get("filings", {}).get("recent", {}) if isinstance(filing_input, dict) else {}
    if isinstance(filings, list): raw_filings = filing_input
    else:
        raw_filings=[]; n=len(recent.get("form", []))
        for i in range(n): raw_filings.append({"accession_number":recent.get("accessionNumber",[None]*n)[i],"form":recent["form"][i],"filing_date":recent.get("filingDate",[None]*n)[i],"report_date":recent.get("reportDate",[None]*n)[i],"acceptance_datetime":recent.get("acceptanceDateTime",[None]*n)[i],"primary_document":recent.get("primaryDocument",[None]*n)[i],"source":"sec_edgar","published_at":recent.get("filingDate",[None]*n)[i],"retrieved_at":filing_input.get("retrieved_at"),"cik":filing_input.get("cik")})
    filtered=0; normalized_filings=[]
    for f in raw_filings:
        if str(f.get("form", "")).strip().upper() not in allowed_forms:
            filtered += 1; excluded_count += 1; filter_counts["non_target_form"]+=1
            continue
        if f.get("cik"):
            if not _CIK.fullmatch(str(f["cik"])): raise SnapshotConflictError("invalid filing CIK")
            if security.get("cik") and str(f["cik"]).zfill(10) != str(security["cik"]).zfill(10): raise SnapshotConflictError("filing CIK conflict in snapshot inputs")
        fd=_day(f.get("filing_date") or f.get("published_at"))
        publication=f.get("published_at") or f.get("filing_date")
        acceptance=f.get("acceptance_datetime")
        if acceptance and len(str(acceptance)) < 12: acceptance=None
        if not (acceptance or publication): filter_counts["filing_availability_unknown"]+=1
        if not _before(acceptance or publication, cutoff): filtered += 1; excluded_count += 1; filter_counts["filing_after_as_of"]+=1; continue
        filing_url=f.get("filing_url") or f.get("source_url")
        if not filing_url and f.get("accession_number") and (f.get("cik") or security["cik"]):
            cik=str(f.get("cik") or security["cik"]).lstrip("0")
            filing_url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{f['accession_number'].replace('-', '')}/{f.get('primary_document') or ''}"
        fcik=f.get("cik") or security["cik"]
        normalized_filings.append({"accession_number":f.get("accession_number"),"form":f.get("form"),"filing_date":f.get("filing_date"),"report_date":f.get("report_date"),"acceptance_datetime":f.get("acceptance_datetime"),"primary_document":f.get("primary_document"),"filing_url":filing_url,"source":f.get("source","sec_edgar"),"published_at":f.get("published_at") or f.get("filing_date"),"retrieved_at":f.get("retrieved_at"),"cik":str(fcik).zfill(10) if fcik else None})
    facts=[]; source_facts=facts_payload.get("facts", facts_payload.get("rows", []))
    if isinstance(source_facts, dict):
        for taxonomy,tags in source_facts.items():
            for tag,info in tags.items():
                for unit,entries in info.get("units",{}).items():
                    for e in entries: facts.append({"taxonomy":taxonomy,"tag":tag,"label":info.get("label"),"description":info.get("description"),"value":e.get("val"),"unit":unit,"currency":unit if unit in {"USD","EUR","GBP","JPY"} else None,"period_start":e.get("start"),"period_end":e.get("end"),"filed_at":e.get("filed"),"available_at":e.get("filed"),"form":e.get("form"),"frame":e.get("frame"),"accession_number":e.get("accn"),"source":"sec_companyfacts","source_url":facts_payload.get("source_url"),"retrieved_at":facts_payload.get("retrieved_at")})
    else: facts=[deepcopy(row) for row in source_facts]
    available=[]
    for fact in facts:
        if not fact.get("available_at"):
            filter_counts["missing_fact_available_at"]+=1; filtered += 1; excluded_count += 1; continue
        if not _before(fact.get("available_at"), cutoff): filtered += 1; excluded_count += 1; filter_counts["fact_after_as_of"]+=1; continue
        available.append(fact)
    sources=[]; seen=set()
    def add(kind, provider, url, retrieved, data_as_of=None, published_at=None, sha=None):
        key=(provider,url,retrieved,sha)
        if key not in seen: seen.add(key); sources.append({"source_id":f"source-{len(sources)+1:03d}","source_type":kind,"provider":provider,"source_url":url,"retrieved_at":retrieved,"data_as_of":data_as_of,"published_at":published_at,"raw_sha256":sha})
    if bars: add("market",market.get("source","unknown"),market.get("source_url"),market.get("retrieved_at"),market_out["data_as_of"],sha=market.get("raw_sha256"))
    if available or normalized_filings: add("sec","sec_edgar",facts_payload.get("source_url"),facts_payload.get("retrieved_at"),sha=facts_payload.get("raw_sha256"))
    missing=[]
    if not bars: missing.append("market_data")
    if not available: missing.append("sec_facts")
    if not normalized_filings: missing.append("sec_filings")
    status="completed" if bars and (available or normalized_filings) else "partial" if bars or available or normalized_filings else "failed"
    run_status="completed" if status != "failed" else "failed"
    result={"schema_version":"1.1","snapshot_id":snapshot_id or _id("snapshot",symbol,cutoff),"snapshot_type":"single_stock_research","created_at":now,"as_of":cutoff,"data_mode":data_mode,"security":security,"market_data":market_out,"sec_filings":normalized_filings,"sec_facts":available,"summary":{"latest_market_observation":latest.get("as_of") if latest else None,"available_fact_count":len(available),"available_filing_count":len(normalized_filings),"evidence_status":"complete" if bars and (available or normalized_filings) else "partial" if (bars or available or normalized_filings) else "insufficient","limitations":["news data unavailable"],"target_forms":sorted(allowed_forms)},"sources":sources,"data_quality":{"status":status,"missing_fields":missing,"missing_sources":missing,"warnings":warnings,"conflicts":conflicts,"point_in_time_filtered_count":filtered,"total_excluded_count":excluded_count,"filter_counts":filter_counts},"run_record":{"run_id":run_id or _id("run",symbol,cutoff),"status":run_status,"started_at":now,"completed_at":now,"input_mode":"fixture" if data_mode=="synthetic" else "saved_snapshot","network_executed":False,"steps":[{"name":"assemble_market","status":"completed" if bars else "skipped"},{"name":"assemble_sec","status":"completed" if (available or normalized_filings) else "skipped"},{"name":"point_in_time_filter","status":"completed"}],"warnings":missing,"errors":[] if status != "failed" else ["no usable market or SEC data"],"model_calls":0}}
    return result
