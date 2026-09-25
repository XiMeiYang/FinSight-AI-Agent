from typing import TypedDict, List
class FilingSection(TypedDict):
 section_id:str; section_title:str; section_order:int; start_offset:int; end_offset:int; text:str; text_sha256:str
class FilingDocument(TypedDict):
 schema_version:str; document_id:str; symbol:str; cik:str; accession_number:str; form:str; filing_date:str|None; report_date:str|None; accepted_at:str|None; published_at:str|None; as_of:str; source_url:str|None; input_file:str; input_sha256:str; parser_version:str; title:str; sections:List[FilingSection]; warnings:List[str]
class EvidenceChunk(TypedDict):
 schema_version:str; chunk_id:str; document_id:str; symbol:str; cik:str; accession_number:str; form:str; filing_date:str|None; accepted_at:str|None; source_url:str|None; section_id:str; section_title:str; chunk_index:int; text:str; character_count:int; text_sha256:str; citation:str
