"""Serializable model helpers for ResearchSnapshot."""
from dataclasses import dataclass, asdict
from typing import Any, Optional

@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_type: str
    provider: str
    source_url: Optional[str]
    retrieved_at: Optional[str]
    data_as_of: Optional[str] = None
    published_at: Optional[str] = None
    raw_sha256: Optional[str] = None

@dataclass(frozen=True)
class ResearchSnapshot:
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
    def to_dict(self): return asdict(self)
