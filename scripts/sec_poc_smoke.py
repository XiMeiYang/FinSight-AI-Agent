"""Run the offline SEC normalization smoke check; no network is used."""
import json, hashlib
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from finsight_sec.client import SECClient
root=Path(__file__).parents[1]; raw=(root/"tests/fixtures/sec_companyfacts.synthetic.json").read_bytes(); payload=json.loads(raw)
result=SECClient.normalize_facts(payload, source_url="fixture://sec_companyfacts.synthetic", raw_sha256=hashlib.sha256(raw).hexdigest())
print(json.dumps({"status":"offline_fixture_ok","cik":result.cik,"facts":len(result.facts),"raw_sha256":result.raw_sha256}))
