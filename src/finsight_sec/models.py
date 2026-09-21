"""Small, source-preserving models for the SEC PoC."""
from dataclasses import dataclass
from typing import Any, Optional

@dataclass(frozen=True)
class Filing:
    accession_number: str
    form: str
    filing_date: str
    report_date: Optional[str]
    acceptance_datetime: Optional[str]
    primary_document: Optional[str]
    filing_url: str
    source: str = "sec_edgar"
    published_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    cik: Optional[str] = None

@dataclass(frozen=True)
class Fact:
    taxonomy: str
    tag: str
    label: Optional[str]
    description: Optional[str]
    unit: str
    value: Any
    start: Optional[str]
    end: Optional[str]
    filed: Optional[str]
    form: Optional[str]
    frame: Optional[str]
    accession_number: Optional[str]

@dataclass(frozen=True)
class NormalizedFact:
    taxonomy: str
    tag: str
    label: Optional[str]
    value: Any
    unit: str
    period_start: Optional[str]
    period_end: Optional[str]
    filed_at: Optional[str]
    available_at: Optional[str]
    form: Optional[str]
    frame: Optional[str]
    source: str
    source_url: str
    accession_number: Optional[str]
    as_of: Optional[str]
    description: Optional[str] = None
    currency: Optional[str] = None
    retrieved_at: Optional[str] = None

@dataclass(frozen=True)
class CompanyFacts:
    cik: str
    entity_name: Optional[str]
    facts: tuple[NormalizedFact, ...]
    retrieved_at: str
    source_url: str
    raw_sha256: str
