"""Deterministic, non-generative presentation helpers for SEC evidence."""
from __future__ import annotations

import re
from typing import Iterable, Mapping

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "did",
    "do", "does", "for", "from", "how", "if", "in", "is", "it", "may", "of",
    "on", "or", "our", "that", "the", "their", "this", "to", "what", "when",
    "which", "who", "why", "with", "would", "you", "your",
}


def _terms(question: str) -> list[str]:
    return list(dict.fromkeys(
        word.lower() for word in _WORD_RE.findall(question or "")
        if word.lower() not in _STOPWORDS and len(word) > 1
    ))


def _trim_sentence(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _bounded_sentence(sentence: str, terms: list[str], limit: int) -> str:
    """Return a bounded window made only of complete source words."""
    words = list(_WORD_RE.finditer(sentence))
    if not words or limit <= 4:
        return "." * max(1, limit)
    hit = next((i for i, match in enumerate(words)
                if any(match.group().lower() == term for term in terms)), 0)
    best = None
    # Grow a window around the strongest first hit in one pass. This avoids
    # quadratic scans on unusually large SEC chunks.
    left = right = hit
    while True:
        candidates = []
        if left > 0:
            candidates.append((left - 1, right))
        if right + 1 < len(words):
            candidates.append((left, right + 1))
        viable = []
        for candidate_left, candidate_right in candidates:
            core = sentence[words[candidate_left].start():words[candidate_right].end()]
            candidate = ("... " if candidate_left else "") + core + (" ..." if candidate_right < len(words) - 1 else "")
            if len(candidate) <= limit:
                viable.append((len(candidate), candidate_left, candidate_right))
        if not viable:
            break
        _, left, right = max(viable)
        best = (left, right)
    if best is None:
        return "..."
    left, right = best
    core = sentence[words[left].start():words[right].end()]
    return ("... " if left else "") + core + (" ..." if right < len(words) - 1 else "")


def make_evidence_excerpt(text: str, question: str, max_length: int = 400) -> dict:
    """Select complete-sentence evidence without changing the source text.

    This is deliberately a presentation operation, not summarization.  It uses
    question-term overlap and deterministic sentence windows only.
    """
    if not isinstance(max_length, int) or max_length < 1:
        raise ValueError("max_length must be positive")
    normalized = _trim_sentence(text)
    terms = _terms(question)
    if not normalized:
        return {"evidence_excerpt": "", "excerpt_truncated": False, "matched_terms": []}

    sentences = [_trim_sentence(item) for item in _SENTENCE_RE.split(normalized) if _trim_sentence(item)]
    if not sentences:
        sentences = [normalized]
    if len(sentences) == 1:
        # With no adjacent sentence, a chunk boundary may contain only a
        # fragment. Its first lowercase token and unterminated last token
        # cannot be verified as complete words, so do not display either.
        fragment = sentences[0]
        leading_edge = bool(re.match(r"^[a-z]", fragment))
        trailing_edge = not bool(re.search(r"[.!?]$", fragment))
        if leading_edge or trailing_edge:
            words = list(_WORD_RE.finditer(fragment))
            first = 1 if leading_edge else 0
            last = len(words) - (1 if trailing_edge else 0)
            core = (fragment[words[first].start():words[last - 1].end()]
                    if first < last else "")
            if core and not trailing_edge:
                core += fragment[words[last - 1].end():]
            if not any(word.lower() not in _STOPWORDS for word in _WORD_RE.findall(core)):
                excerpt = "." * min(3, max_length)
            else:
                room = max_length - (4 if leading_edge else 0) - (4 if trailing_edge else 0)
                clipped = _bounded_sentence(core, terms, room) if len(core) > room else core
                excerpt = ("... " if leading_edge else "") + clipped + (" ..." if trailing_edge else "")
                if len(excerpt) > max_length:
                    excerpt = "." * min(3, max_length)
            matched = [term for term in terms if re.search(r"\b" + re.escape(term) + r"\b", excerpt, re.I)]
            return {"evidence_excerpt": excerpt, "excerpt_truncated": True, "matched_terms": matched}
    # SEC chunks can begin/end in the middle of a sentence. Prefer complete
    # sentence windows when another sentence is available, rather than showing
    # an unhelpful leading/trailing fragment.
    first_is_fragment = not re.match(r"^[A-Z0-9\"'(]", sentences[0])
    if len(sentences) > 1 and first_is_fragment:
        sentences = sentences[1:]
    if len(sentences) > 1 and not re.search(r"[.!?]\s*$", sentences[-1]):
        sentences = sentences[:-1]
    # A period inside a filing heading (for example "Item 1A.") can make a
    # following quote-closing fragment look like a new sentence.
    complete_candidates = [sentence for sentence in sentences
                           if not ("”" in sentence[:80] and "“" not in sentence[:80])]
    if complete_candidates:
        sentences = complete_candidates
    scores = [sum(term in {x.lower() for x in _WORD_RE.findall(sentence)} for term in terms)
              for sentence in sentences]
    best = max(range(len(sentences)), key=lambda index: (scores[index], -index))
    chosen = [best]
    # Add adjacent context only when the complete sentence window fits.
    for neighbour in (best - 1, best + 1):
        if 0 <= neighbour < len(sentences):
            candidate = " ".join(sentences[index] for index in sorted(chosen + [neighbour]))
            if len(candidate) <= max_length:
                chosen.append(neighbour)
    excerpt = " ".join(sentences[index] for index in sorted(chosen))
    matched = [term for term in terms if re.search(r"\b" + re.escape(term) + r"\b", excerpt, re.I)]
    if len(excerpt) <= max_length:
        return {"evidence_excerpt": excerpt, "excerpt_truncated": False, "matched_terms": matched}

    if max_length <= 4:
        return {"evidence_excerpt": "." * max_length, "excerpt_truncated": True, "matched_terms": []}

    # A sentence longer than the display budget is clipped at a word boundary.
    # Prefer the start of the selected sentence; if a hit is later, center a
    # bounded window around it while retaining an explicit ellipsis boundary.
    sentence = sentences[best]
    excerpt = _bounded_sentence(sentence, terms, max_length)
    if excerpt != "..." and not excerpt.endswith("..."):
        while len(excerpt) + 4 > max_length and " " in excerpt:
            excerpt = excerpt.rsplit(" ", 1)[0]
        excerpt = excerpt.rstrip() + " ..." if len(excerpt) + 4 <= max_length else "..."
    matched = [term for term in terms if re.search(r"\b" + re.escape(term) + r"\b", excerpt, re.I)]
    return {"evidence_excerpt": excerpt, "excerpt_truncated": True, "matched_terms": matched}


def present_results(results: Iterable[Mapping], rows: Iterable[Mapping], question: str,
                    max_length: int = 400) -> list[dict]:
    """Attach deterministic excerpts to already-ranked results."""
    catalog = {row.get("chunk_id"): row for row in rows}
    output = []
    for result in results:
        item = dict(result)
        source = catalog.get(item.get("chunk_id"))
        if source is None or not source.get("text"):
            raise ValueError("retrieval result is outside the loaded corpus")
        item.update(make_evidence_excerpt(source.get("text", item.get("evidence_preview", "")), question, max_length))
        item["section_title"] = source.get("section_title", item.get("section_title", item.get("section")))
        output.append(item)
    return output
