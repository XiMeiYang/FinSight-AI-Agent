#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

def main():
    parser = argparse.ArgumentParser(description="Run the offline FinSight SEC evidence app")
    parser.add_argument("--bm25-index", required=True); parser.add_argument("--dense-index", required=True)
    parser.add_argument("--corpus", required=True); parser.add_argument("--model-cache", required=True)
    parser.add_argument("--model-revision", required=True); parser.add_argument("--model-name", default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("host must be loopback-only")
    try:
        import uvicorn
        from finsight_app.api import create_app
        from finsight_app.retrieval_service import RetrievalService
        service = RetrievalService(args.bm25_index, args.dense_index, args.corpus, args.model_cache, args.model_revision, args.model_name)
        app = create_app(service, ROOT / "prototype")
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    except Exception as exc:
        print("local app could not start: dependency or offline corpus validation failed", file=sys.stderr)
        raise SystemExit(2) from exc
if __name__ == "__main__": main()
