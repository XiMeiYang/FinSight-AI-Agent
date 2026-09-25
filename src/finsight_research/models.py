"""Type contract for the JSON dictionary returned by snapshot builder."""
from typing import Any, Optional, TypedDict

class SourceRecord(TypedDict, total=False):
    source_id: str
    source_type: str
    provider: str
    source_url: Optional[str]
    retrieved_at: Optional[str]
    data_as_of: Optional[str] = None
    published_at: Optional[str] = None
    raw_sha256: Optional[str] = None
    normalized_sha256: Optional[str]
    input_file: Optional[str]

class SecurityRecord(TypedDict, total=False):
    symbol: str
    company_name: Optional[str]
    cik: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    ticker_mapping: dict[str, Any]

class ResearchSnapshot(TypedDict):
    schema_version: str
    snapshot_id: str
    snapshot_type: str
    created_at: str
    as_of: str
    data_mode: str
    security: SecurityRecord
    market_data: dict[str, Any]
    sec_filings: list[dict[str, Any]]
    sec_facts: list[dict[str, Any]]
    summary: dict[str, Any]
    sources: list[SourceRecord]
    data_quality: dict[str, Any]
    run_record: dict[str, Any]
