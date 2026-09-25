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

class FilterCounts(TypedDict, total=False):
    non_target_form: int
    market_after_as_of: int
    market_missing_timestamp: int
    filing_after_as_of: int
    fact_after_as_of: int
    missing_fact_available_at: int
    filing_availability_unknown: int

class DataQuality(TypedDict, total=False):
    status: str
    missing_fields: list[str]
    missing_sources: list[str]
    warnings: list[str]
    conflicts: list[str]
    point_in_time_filtered_count: int
    total_excluded_count: int
    filter_counts: FilterCounts

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
    data_quality: DataQuality
    run_record: dict[str, Any]
