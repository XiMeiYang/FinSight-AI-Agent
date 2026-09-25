#!/usr/bin/env python3
import argparse,hashlib,json,sys
from pathlib import Path
from finsight_rag import clean_html,identify_sections,chunk_sections
def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--metadata',required=True); p.add_argument('--symbol',required=True); p.add_argument('--as-of',required=True); p.add_argument('--output-dir',required=True); a=p.parse_args()
 root=Path('.local_data').resolve(); ip=Path(a.input); mp=Path(a.metadata)
 for x in (ip,mp):
  if x.is_symlink() or root not in x.resolve().parents: raise ValueError('input must be a non-symlink file inside .local_data')
 raw=ip.read_bytes(); text=clean_html(raw.decode('utf-8')); sections=identify_sections(text); chunks=chunk_sections(sections)
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); docid=hashlib.sha256(raw).hexdigest()[:20]
 for c in chunks: c.update(document_id=docid,symbol=a.symbol.upper(),as_of=a.as_of,citation=f"{a.symbol.upper()} filing section {c['section_title']} chunk {c['chunk_index']}")
 (out/'chunks.jsonl').write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in chunks)+'\n'); print(json.dumps({'document_id':docid,'section_count':len(sections),'chunk_count':len(chunks),'input_sha256':hashlib.sha256(raw).hexdigest(),'network_executed':False,'model_calls':0}))
if __name__=='__main__':
 try: main()
 except Exception as e: print(f'error: {e}',file=sys.stderr); raise SystemExit(2)
