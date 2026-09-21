"""Explicit Alpha Vantage PoC runner; network is opt-in."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from finsight_market.alpha_vantage import AlphaVantageClient, AlphaVantageConfig, MarketDataError

def main():
    p = argparse.ArgumentParser(); p.add_argument("symbol"); p.add_argument("--network", action="store_true"); p.add_argument("--outputsize", choices=["compact", "full"], default="compact"); args = p.parse_args()
    if not args.network:
        print("network disabled; pass --network explicitly", file=sys.stderr); return 2
    client = AlphaVantageClient(AlphaVantageConfig.from_environment(outputsize=args.outputsize))
    try:
        result = client.fetch_daily(args.symbol)
        normalized = client.normalize(result["payload"], symbol=result["symbol"], source_url=client.config.base_url, retrieved_at=result["metadata"]["retrieved_at"])
        raw_path, normalized_path = client.save_payloads(symbol=result["symbol"], raw=result["raw"], normalized=normalized, retrieved_at=result["metadata"]["retrieved_at"])
        print(json.dumps({"metadata": result["metadata"], "raw_sha256": client.raw_sha256(result["raw"]), "raw_path": str(raw_path), "normalized_path": str(normalized_path), "normalized_count": len(normalized["rows"])}, ensure_ascii=False, indent=2)); return 0
    except MarketDataError as exc:
        print(json.dumps({"error": str(exc), "category": exc.category, "status": exc.status}, ensure_ascii=False), file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
