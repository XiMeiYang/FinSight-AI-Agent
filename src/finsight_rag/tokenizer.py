"""Deterministic, dependency-free tokenizer for financial retrieval."""
from __future__ import annotations
import re, unicodedata
TOKENIZER_VERSION = "financial-v1"
_NUM = re.compile(r"(?<!\w)\$?\d[\d,]*(?:\.\d+)?%?(?!\w)")
_WORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_HYPHENS = "‐‑‒–—−﹘﹣－"
def tokenize(text: str, *, max_query_chars: int | None = None) -> list[str]:
    if not isinstance(text, str): raise ValueError("query must be text")
    if max_query_chars is not None and len(text) > max_query_chars: raise ValueError("query too long")
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.translate(str.maketrans({c:"-" for c in _HYPHENS}))
    out=[]
    covered=[]
    for m in _NUM.finditer(text):
        token=m.group(0).replace("$", "").replace(",", "")
        out.append(token); covered.append((m.start(),m.end()))
    for m in _WORD.finditer(text):
        if any(a < m.end() and m.start() < b for a,b in covered): continue
        token=m.group(0)
        out.append(token)
        if "-" in token: out.extend(p for p in token.split("-") if p)
    return out
def validate_query(query: str, *, max_query_chars: int = 2000) -> list[str]:
    tokens=tokenize(query,max_query_chars=max_query_chars)
    if not tokens: raise ValueError("query has no searchable tokens")
    return tokens
