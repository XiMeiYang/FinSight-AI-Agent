"""Small, offline-first Alpha Vantage daily OHLCV adapter.

The client never reads a key from a function argument or logs it. Network use is
explicit and requires FINSIGHT_MARKET_API_KEY.
"""
from __future__ import annotations

import hashlib, json, logging, os, time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

LOG = logging.getLogger("finsight.market")

class MarketDataError(Exception):
    def __init__(self, message: str, *, category: str, status: Optional[int] = None, retryable: bool = False):
        super().__init__(message); self.category = category; self.status = status; self.retryable = retryable

@dataclass(frozen=True)
class AlphaVantageConfig:
    base_url: str = "https://www.alphavantage.co/query"
    api_key: Optional[str] = None
    timeout_seconds: float = 10.0
    max_retries: int = 2
    outputsize: str = "compact"
    sleep: Callable[[float], None] = time.sleep

    @classmethod
    def from_environment(cls, **kwargs):
        return cls(api_key=os.getenv("FINSIGHT_MARKET_API_KEY"), **kwargs)

class AlphaVantageClient:
    def __init__(self, config: Optional[AlphaVantageConfig] = None, opener: Callable = urlopen):
        self.config = config or AlphaVantageConfig.from_environment(); self._opener = opener
        self.request_metadata = []

    def _require_key(self):
        if not self.config.api_key:
            raise MarketDataError("FINSIGHT_MARKET_API_KEY is required; network access stopped", category="missing_key")

    def fetch_daily(self, symbol: str) -> dict:
        self._require_key()
        symbol = symbol.strip().upper()
        if not symbol or len(symbol) > 20:
            raise MarketDataError("invalid symbol", category="invalid_input")
        if self.config.outputsize not in {"compact", "full"}:
            raise MarketDataError("outputsize must be compact or full", category="invalid_input")
        query = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": self.config.outputsize, "apikey": self.config.api_key}
        url = self.config.base_url + "?" + urlencode(query)
        if not self._allowed(url): raise MarketDataError("Alpha Vantage URL allowlist rejected request", category="blocked_url")
        request = Request(url, headers={"Accept": "application/json"})
        for attempt in range(self.config.max_retries + 1):
            started = time.monotonic()
            try:
                with self._opener(request, timeout=self.config.timeout_seconds) as response:
                    raw = response.read(); status = getattr(response, "status", getattr(response, "code", None)); final = response.geturl()
                if not self._allowed(final): raise MarketDataError("redirect outside allowlist", category="blocked_url")
                payload = json.loads(raw.decode("utf-8"))
                self.request_metadata.append(self._meta(url, final, status, started, attempt, None))
                if "Error Message" in payload: raise MarketDataError("provider rejected request", category="provider_error")
                if "Note" in payload:
                    err = MarketDataError("provider rate limit response", category="rate_limited", retryable=True)
                    self.request_metadata[-1]["retry_reason"] = "rate_limited"
                    if attempt == self.config.max_retries: raise err
                    self.config.sleep(min(2 ** attempt, 8)); continue
                if not any(k.startswith("Time Series") for k in payload): raise MarketDataError("daily series missing", category="empty_payload")
                return {"raw": raw, "payload": payload, "metadata": self.request_metadata[-1], "symbol": symbol}
            except HTTPError as exc:
                retryable = exc.code == 429 or exc.code >= 500; category = "rate_limited" if exc.code == 429 else ("server_error" if exc.code >= 500 else "http_error")
                self.request_metadata.append(self._meta(url, url, exc.code, started, attempt, category))
                if not retryable or attempt == self.config.max_retries: raise MarketDataError(f"provider HTTP {exc.code}", category=category, status=exc.code, retryable=retryable) from exc
            except (TimeoutError, URLError) as exc:
                category = "timeout" if isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError) else "network_error"
                self.request_metadata.append(self._meta(url, url, None, started, attempt, category))
                if attempt == self.config.max_retries: raise MarketDataError("provider request failed", category=category, retryable=True) from exc
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise MarketDataError("invalid provider JSON", category="invalid_payload") from exc
            self.config.sleep(min(2 ** attempt, 8))
        raise AssertionError("unreachable")

    @staticmethod
    def normalize(payload: dict, *, symbol: str, retrieved_at: Optional[str] = None, source_url: str = "") -> dict:
        series_key = next((k for k in payload if k.startswith("Time Series")), None)
        if not series_key: raise MarketDataError("daily series missing", category="empty_payload")
        if not payload[series_key]: raise MarketDataError("daily series is empty", category="empty_payload")
        rows = []; seen = set()
        for day, values in payload[series_key].items():
            try: parsed_day = datetime.strptime(day, "%Y-%m-%d").date()
            except (TypeError, ValueError) as exc: raise MarketDataError("invalid trading date", category="invalid_date") from exc
            if day in seen: raise MarketDataError("duplicate trading date", category="duplicate_date")
            seen.add(day)
            try:
                vals = {name: Decimal(str(values[key])) for name, key in (("open", "1. open"), ("high", "2. high"), ("low", "3. low"), ("close", "4. close"), ("volume", "5. volume"))}
            except (KeyError, InvalidOperation, ValueError) as exc: raise MarketDataError("invalid OHLCV value", category="invalid_type") from exc
            if any(not v.is_finite() for v in vals.values()): raise MarketDataError("non-finite OHLCV value", category="invalid_type")
            if any(vals[k] <= 0 for k in ("open", "high", "low", "close")) or vals["volume"] < 0: raise MarketDataError("negative or zero price", category="invalid_range")
            if vals["volume"] != vals["volume"].to_integral_value(): raise MarketDataError("volume must be integer", category="invalid_type")
            if vals["high"] < max(vals["open"], vals["close"]) or vals["low"] > min(vals["open"], vals["close"]) or vals["low"] > vals["high"]:
                raise MarketDataError("invalid OHLCV relationship", category="invalid_range")
            row = {"symbol": symbol.upper(), "as_of": day, "timestamp": day + "T00:00:00Z", "open": float(vals["open"]), "high": float(vals["high"]), "low": float(vals["low"]), "close": float(vals["close"]), "volume": int(vals["volume"]), "adjusted_close": None, "currency": None, "source": "alpha_vantage", "source_url": source_url, "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat()}
            rows.append(row)
        rows.sort(key=lambda x: x["as_of"])
        return {"symbol": symbol.upper(), "source": "alpha_vantage", "currency": None, "rows": rows, "retrieved_at": rows[0]["retrieved_at"] if rows else retrieved_at}

    @staticmethod
    def raw_sha256(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def save_payloads(*, symbol: str, raw: bytes, normalized: dict, retrieved_at: str, root: str = ".local_data/market"):
        base = Path(root); (base / "raw").mkdir(parents=True, exist_ok=True); (base / "normalized").mkdir(parents=True, exist_ok=True)
        stem = f"{symbol.upper()}_{retrieved_at.replace(':','').replace('+','_')}"; rp = base / "raw" / (stem + ".json"); np = base / "normalized" / (stem + ".json")
        if not rp.exists(): rp.write_bytes(raw)
        if not np.exists(): np.write_text(json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        return rp, np

    @staticmethod
    def _allowed(url: str) -> bool: return urlparse(url).scheme == "https" and urlparse(url).netloc.lower() == "www.alphavantage.co"
    @staticmethod
    def _meta(requested, final, status, started, attempt, reason):
        elapsed = round((time.monotonic() - started) * 1000, 3)
        return {"requested_url": requested.split("apikey=")[0] + "apikey=[REDACTED]", "final_url": final.split("apikey=")[0] + "apikey=[REDACTED]", "http_status": status, "elapsed_ms": elapsed, "attempt_count": attempt + 1, "retry_count": attempt, "retry_reason": reason, "retrieved_at": datetime.now(timezone.utc).isoformat()}
