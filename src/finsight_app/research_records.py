from __future__ import annotations
import hashlib, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import threading
import os
import stat

SCHEMA_VERSION = 1
_FIELDS = ("record_id","created_at","symbol","question","answer_status","save_status","review_status")

class ResearchRecordError(RuntimeError): pass
class ResearchRecordNotFound(ResearchRecordError): pass
class ResearchRecordCorrupt(ResearchRecordError): pass

class ResearchRecordStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        parent = self.path.parent
        # Never follow or chmod symlinked paths. New private parents are created safely.
        parent = parent.absolute()
        # Check every existing component, including intermediate ancestors.
        components = parent.parts
        current = Path(components[0])
        for component in components[1:]:
            current = current / component
            if current.exists() or current.is_symlink():
                if stat.S_ISLNK(os.lstat(current).st_mode):
                    # macOS commonly exposes temporary directories through /var -> /private/var.
                    if current in (Path("/var"), Path("/tmp")):
                        continue
                    raise ResearchRecordError("research record directory symlink is not allowed")
        probe = parent
        missing = []
        while not probe.exists():
            missing.append(probe); probe = probe.parent
        if missing:
            parent.mkdir(parents=True, exist_ok=True)
            for created in missing: os.chmod(created, 0o700)
        elif stat.S_IMODE(parent.stat().st_mode) != 0o700:
            raise ResearchRecordError("research record directory permissions must be 0700")
        if self.path.exists() and self.path.is_symlink(): raise ResearchRecordError("research record database symlink is not allowed")
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd)
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._lock = threading.RLock()
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("CREATE TABLE IF NOT EXISTS research_records (record_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, symbol TEXT NOT NULL, question TEXT NOT NULL, answer_status TEXT NOT NULL, save_status TEXT NOT NULL, review_status TEXT NOT NULL, schema_version INTEGER NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL)")
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_research_records_symbol_created ON research_records(symbol, created_at DESC)")
        self._db.commit()
        os.chmod(self.path, 0o600)

    def close(self): self._db.close()
    @staticmethod
    def _now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    @staticmethod
    def _payload(data):
        raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return raw, hashlib.sha256(raw.encode()).hexdigest()
    def save(self, *, symbol: str, question: str, answer_status: str, answer: Any, citations: Any, evidence: Any, filters: Any = None, generation: Any = None, packed_evidence: Any = None, model_metadata: Any = None) -> dict[str, Any]:
        rid = str(uuid.uuid4()); created = self._now()
        payload = {"schema_version": SCHEMA_VERSION, "data_as_of": (filters or {}).get("as_of"), "filters": filters or {}, "answer": answer, "citations": citations or [], "evidence": evidence or [], "packed_evidence": packed_evidence or [], "generation": generation or {}, "model_metadata": model_metadata or {}, "symbol": symbol, "question": question}
        raw, digest = self._payload(payload)
        with self._lock, self._db:
            self._db.execute("INSERT INTO research_records VALUES (?,?,?,?,?,?,?,?,?,?)", (rid, created, symbol, question, answer_status, "saved", "pending_human_review", SCHEMA_VERSION, raw, digest))
        return {"record_id": rid, "save_status": "saved", "review_status": "pending_human_review"}
    def save_failure(self, *, symbol: str, question: str, detail: str) -> dict[str, Any]:
        rid = str(uuid.uuid4()); created = self._now(); payload = {"schema_version": SCHEMA_VERSION, "filters": {}, "answer": {"error": detail}, "citations": [], "evidence": [], "packed_evidence": [], "generation": {}, "model_metadata": {}}
        raw, digest = self._payload(payload)
        with self._lock, self._db:
            self._db.execute("INSERT INTO research_records VALUES (?,?,?,?,?,?,?,?,?,?)", (rid, created, symbol, question, "failed", "saved", "not_reviewed", SCHEMA_VERSION, raw, digest))
        return {"record_id": rid, "save_status": "saved", "review_status": "not_reviewed"}
    def _verify(self, row):
        if row["schema_version"] != SCHEMA_VERSION: raise ResearchRecordCorrupt("unsupported research record version")
        try: payload = json.loads(row["payload_json"])
        except Exception as exc: raise ResearchRecordCorrupt("corrupt research record payload") from exc
        _, digest = self._payload(payload)
        if digest != row["payload_sha256"] or payload.get("schema_version") != SCHEMA_VERSION: raise ResearchRecordCorrupt("research record integrity check failed")
        return payload
    def _public(self, row, detail=False):
        item = {k: row[k] for k in _FIELDS}
        if detail:
            p = self._verify(row)
            item["data_as_of"] = p.get("data_as_of")
            item.update({k: p.get(k, {} if k == "filters" else []) for k in ("filters","answer","citations","evidence")})
            item["model_metadata"] = p.get("model_metadata", {})
            item["generation"] = p.get("generation", {})
            item["packed_evidence"] = p.get("packed_evidence", [])
        return item
    def list(self, symbol: str | None = None, limit: int = 20, offset: int = 0):
        limit = max(1, min(int(limit), 100)); offset = max(0, int(offset)); where = " WHERE symbol = ?" if symbol else ""; args = (symbol,) if symbol else ()
        with self._lock:
            total = self._db.execute("SELECT COUNT(*) FROM research_records" + where, args).fetchone()[0]
            rows = self._db.execute("SELECT * FROM research_records" + where + " ORDER BY created_at DESC LIMIT ? OFFSET ?", args + (limit, offset)).fetchall()
        return {"items": [self._public(r) for r in rows], "total": total, "limit": limit, "offset": offset}
    def get(self, record_id: str):
        with self._lock:
            row = self._db.execute("SELECT * FROM research_records WHERE record_id = ?", (record_id,)).fetchone()
        if row is None: raise ResearchRecordNotFound("research record not found")
        return self._public(row, True)
