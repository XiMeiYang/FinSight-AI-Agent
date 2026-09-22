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

class ResearchSnapshot(TypedDict):
    schema_version: str
    snapshot_id: str
    snapshot_type: str
    created_at: str
    as_of: str
    data_mode: str
    security: dict[str, Any]
    market_data: dict[str, Any]
    sec_filings: list[dict[str, Any]]
    sec_facts: list[dict[str, Any]]
    summary: dict[str, Any]
    sources: list[dict[str, Any]]
    data_quality: dict[str, Any]
    run_record: dict[str, Any]
