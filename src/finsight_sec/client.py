"""SEC EDGAR client with explicit network policy and deterministic normalization."""
from __future__ import annotations
import hashlib, json, logging, os, time
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .models import CompanyFacts, Fact, Filing, NormalizedFact

LOG = logging.getLogger("finsight.sec")

class SECError(Exception): pass
class SECRequestError(SECError):
    def __init__(self, message: str, *, category: str, status: Optional[int] = None, retryable: bool = False):
        super().__init__(message); self.category = category; self.status = status; self.retryable = retryable

@dataclass(frozen=True)
class SECConfig:
    base_url: str = "https://data.sec.gov"
    user_agent: Optional[str] = None
    timeout_seconds: float = 10.0
    max_retries: int = 2
    min_interval_seconds: float = 0.2
    sleep: Callable[[float], None] = time.sleep

    @classmethod
    def from_environment(cls, **kwargs) -> "SECConfig":
        return cls(user_agent=os.getenv("FINSIGHT_SEC_USER_AGENT"), **kwargs)

class SECClient:
    """Fetches SEC JSON only when a descriptive User-Agent is explicitly configured."""
    def __init__(self, config: Optional[SECConfig] = None, opener: Callable = urlopen):
        self.config = config or SECConfig.from_environment()
        self._opener = opener
        self._last_request = 0.0
        self.attempts_total = 0

    def _require_agent(self):
        if not self.config.user_agent or "@" not in self.config.user_agent:
            raise SECError("FINSIGHT_SEC_USER_AGENT must be set to a descriptive name and email before network access")

    def _get_json(self, path: str) -> tuple[dict, bytes, str]:
        self._require_agent()
        wait = self.config.min_interval_seconds - (time.monotonic() - self._last_request)
        if wait > 0: self.config.sleep(wait)
        url = path if path.startswith("http") else self.config.base_url.rstrip("/") + "/" + path.lstrip("/")
        if not self._sec_url(url):
            raise SECRequestError("SEC URL allowlist rejected request", category="blocked_url", retryable=False)
        request = Request(url, headers={"User-Agent": self.config.user_agent, "Accept-Encoding": "gzip", "Host": url.split('/')[2]})
        attempts = self.config.max_retries + 1
        for attempt in range(attempts):
            self.attempts_total += 1
            self._last_request = time.monotonic()
            try:
                with self._opener(request, timeout=self.config.timeout_seconds) as response:
                    raw = response.read()
                return json.loads(raw.decode("utf-8")), raw, url
            except HTTPError as exc:
                status = exc.code
                retryable = status == 429 or status >= 500
                category = "rate_limited" if status == 429 else ("server_error" if status >= 500 else "http_error")
                LOG.warning("sec_request_failed", extra={"event": "sec_request_failed", "status": status, "category": category, "attempt": attempt + 1})
                if not retryable or attempt == attempts - 1:
                    raise SECRequestError(f"SEC request failed with HTTP {status}", category=category, status=status, retryable=retryable) from exc
            except (TimeoutError, URLError) as exc:
                if isinstance(exc, URLError) and not isinstance(exc.reason, TimeoutError): category = "network_error"
                else: category = "timeout"
                if attempt == attempts - 1:
                    raise SECRequestError("SEC request failed", category=category, retryable=True) from exc
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise SECRequestError("SEC returned invalid JSON", category="invalid_payload") from exc
            self.config.sleep(min(2 ** attempt, 8))
        raise AssertionError("unreachable")

    def ticker_to_cik(self, ticker: str, mapping: Optional[Mapping[str, str]] = None) -> str:
        if mapping is None:
            data, _, _ = self._get_json("/files/company_tickers.json")
            mapping = {str(v.get("ticker", "")).upper(): str(v["cik_str"]).zfill(10) for v in data.values()}
        cik = mapping.get(ticker.strip().upper())
        if not cik: raise SECError(f"Unknown SEC ticker: {ticker}")
        return str(cik).zfill(10)

    def submissions(self, cik: str) -> dict:
        data, _, _ = self._get_json(f"/submissions/CIK{str(cik).zfill(10)}.json")
        return data

    def company_facts(self, cik: str) -> tuple[dict, bytes, str]:
        return self._get_json(f"/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json")

    def download_raw(self, url: str) -> tuple[bytes, str]:
        """Download an original filing payload without parsing or rewriting it."""
        self._require_agent()
        if not self._sec_url(url):
            raise SECRequestError("filing URL is outside SEC allowlist", category="blocked_url", retryable=False)
        wait = self.config.min_interval_seconds - (time.monotonic() - self._last_request)
        if wait > 0: self.config.sleep(wait)
        request = Request(url, headers={"User-Agent": self.config.user_agent, "Accept-Encoding": "gzip"})
        for attempt in range(self.config.max_retries + 1):
            self.attempts_total += 1
            try:
                self._last_request = time.monotonic()
                with self._opener(request, timeout=self.config.timeout_seconds) as response:
                    raw = response.read()
                return raw, self.raw_sha256(raw)
            except HTTPError as exc:
                category = "rate_limited" if exc.code == 429 else ("server_error" if exc.code >= 500 else "http_error")
                retryable = exc.code == 429 or exc.code >= 500
                if not retryable or attempt == self.config.max_retries:
                    raise SECRequestError(f"SEC filing download failed with HTTP {exc.code}", category=category, status=exc.code, retryable=retryable) from exc
            except (TimeoutError, URLError) as exc:
                if attempt == self.config.max_retries: raise SECRequestError("SEC filing download failed", category="timeout", retryable=True) from exc
            self.config.sleep(min(2 ** attempt, 8))
        raise AssertionError("unreachable")

    @staticmethod
    def select_filings(submissions: dict, forms: Iterable[str] = ("10-K", "10-Q", "8-K"), as_of: Optional[str] = None, retrieved_at: Optional[str] = None) -> list[Filing]:
        recent = submissions.get("filings", {}).get("recent", {})
        allowed = set(forms); out = []
        n = len(recent.get("form", []))
        for i in range(n):
            form = recent["form"][i]; filing_date = recent["filingDate"][i]
            if form not in allowed or (as_of and filing_date > as_of): continue
            acc = recent["accessionNumber"][i]; doc = recent.get("primaryDocument", [None] * n)[i]
            cik = str(submissions.get("cik", "")).zfill(10)
            out.append(Filing(acc, form, filing_date, recent.get("reportDate", [None] * n)[i], recent.get("acceptanceDateTime", [None] * n)[i], doc, f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}" if doc else f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/", cik=cik, published_at=filing_date, retrieved_at=retrieved_at))
        return out

    @staticmethod
    def normalize_facts(payload: dict, *, as_of: Optional[str] = None, source_url: str = "", retrieved_at: Optional[str] = None, raw_sha256: Optional[str] = None) -> CompanyFacts:
        retrieved_at = retrieved_at or datetime.now(timezone.utc).isoformat(); rows = []
        for taxonomy, tags in payload.get("facts", {}).items():
            for tag, info in tags.items():
                for unit, entries in info.get("units", {}).items():
                    for e in entries:
                        available = e.get("filed")
                        if as_of and (not available or available > as_of): continue
                        currency = unit if unit in {"USD", "EUR", "GBP", "JPY"} else None
                        rows.append(NormalizedFact(taxonomy, tag, info.get("label"), e.get("val"), unit, e.get("start"), e.get("end"), e.get("filed"), available, e.get("form"), e.get("frame"), "sec_companyfacts", source_url, e.get("accn"), as_of, info.get("description"), currency, retrieved_at))
        return CompanyFacts(str(payload.get("cik", "")).zfill(10), payload.get("entityName"), tuple(rows), retrieved_at, source_url, raw_sha256 or hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest())

    @staticmethod
    def raw_sha256(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _sec_url(url: str) -> bool:
        from urllib.parse import urlparse
        p=urlparse(url); return p.scheme == "https" and p.netloc.lower() in {"www.sec.gov", "sec.gov", "data.sec.gov"}

    def save_payloads(self, *, cik: str, kind: str, raw: bytes, normalized: object, retrieved_at: str, root: str = ".local_data/sec") -> tuple[Path, Path]:
        base=Path(root); raw_dir=base/"raw"; norm_dir=base/"normalized"; raw_dir.mkdir(parents=True, exist_ok=True); norm_dir.mkdir(parents=True, exist_ok=True)
        digest=self.raw_sha256(raw); stem=f"{str(cik).zfill(10)}_{kind}_{retrieved_at.replace(':','').replace('+','_')}"
        raw_path=raw_dir/(stem+".bin"); norm_path=norm_dir/(stem+".json")
        if not raw_path.exists(): raw_path.write_bytes(raw)
        if not norm_path.exists(): norm_path.write_text(json.dumps(normalized, default=lambda o: o.__dict__, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        return raw_path,norm_path
