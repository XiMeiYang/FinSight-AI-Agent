#!/usr/bin/env python3
"""Build one offline SEC document, chunks and manifest atomically."""
from __future__ import annotations
import argparse,hashlib,json,os,sys,tempfile
from pathlib import Path
from finsight_rag import build_sec_ingestion

def safe(path, root, max_bytes=50*1024*1024):
    root=Path(root).resolve(); p=Path(path)
    if not p.is_absolute(): p=(Path.cwd()/p)
    if p.is_symlink() or not p.is_file(): raise ValueError('unsafe input path')
    resolved=p.resolve()
    if root not in resolved.parents: raise ValueError('unsafe input path')
    if resolved.stat().st_size>max_bytes: raise ValueError('input file too large')
    return resolved

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--metadata',required=True); p.add_argument('--symbol',required=True); p.add_argument('--as-of',required=True); p.add_argument('--output-dir',required=True); p.add_argument('--overwrite',action='store_true'); a=p.parse_args()
    root=Path('.local_data').resolve(); ip=safe(a.input,root); mp=safe(a.metadata,root)
    raw=ip.read_bytes(); meta=json.loads(mp.read_text(encoding='utf-8')); rel=str(ip.relative_to(root))
    doc,chunks,man=build_sec_ingestion(raw,meta,a.symbol,a.as_of,input_file=rel,input_sha256=hashlib.sha256(raw).hexdigest())
    out=Path(a.output_dir).resolve()
    if root not in out.parents and out!=root: raise ValueError('unsafe output path')
    out.mkdir(parents=True,exist_ok=True); dirs=[out/'documents',out/'chunks',out/'manifests']
    for d in dirs: d.mkdir(exist_ok=True)
    did=doc['document_id']; files=[dirs[0]/f'{did}.json',dirs[1]/f'{did}.jsonl',dirs[2]/f'{did}.json']
    if any(x.exists() for x in files) and not a.overwrite: raise ValueError('output exists')
    payloads=[json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2).encode(), ('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in chunks)+'\n').encode()]
    man.update(document_file=str(files[0].relative_to(root)),chunks_file=str(files[1].relative_to(root)),manifest_file=str(files[2].relative_to(root)),document_sha256=hashlib.sha256(payloads[0]).hexdigest(),chunks_sha256=hashlib.sha256(payloads[1]).hexdigest())
    payloads.append(json.dumps(man,ensure_ascii=False,sort_keys=True,indent=2).encode())
    tmpdir=Path(tempfile.mkdtemp(prefix='.sec-batch-',dir=str(out)))
    try:
        for f,data in zip(files,payloads): (tmpdir/f.name).write_bytes(data)
        for f in files:
            tmpdir.joinpath(f.name).replace(f)
    finally:
        try: tmpdir.rmdir()
        except OSError: pass
    print(json.dumps({'document_id':did,'symbol':doc['symbol'],'form':doc['form'],'accession_number':doc['accession_number'],'section_count':len(doc['sections']),'chunk_count':len(chunks),'input_sha256':doc['input_sha256'],'document_sha256':man['document_sha256'],'chunks_sha256':man['chunks_sha256'],'network_executed':False,'model_calls':0}))
if __name__=='__main__':
    try: main()
    except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
