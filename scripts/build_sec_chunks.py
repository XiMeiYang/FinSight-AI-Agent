#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,sys,tempfile
from pathlib import Path
from finsight_rag import build_sec_ingestion

def safe(path,root,max_bytes=50*1024*1024):
    root=Path(root).resolve(); p=Path(path)
    if not p.is_absolute(): p=Path.cwd()/p
    if p.is_symlink() or not p.is_file(): raise ValueError('unsafe input path')
    q=p.resolve()
    if root not in q.parents or q.stat().st_size>max_bytes: raise ValueError('unsafe input path')
    return q

def write_batch(files,payloads,overwrite):
    if any(f.is_symlink() or (f.exists() and not overwrite) for f in files): raise ValueError('output exists or is symlink')
    root=files[0].parents[2]; tmp=Path(tempfile.mkdtemp(prefix='.sec-batch-',dir=str(root)))
    try:
        for rel,data in zip(('documents/'+files[0].name,'chunks/'+files[1].name,'manifests/'+files[2].name),payloads):
            dest=tmp/rel; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
        d=json.loads((tmp/'documents'/files[0].name).read_text()); c=[json.loads(x) for x in (tmp/'chunks'/files[1].name).read_text().splitlines() if x]; m=json.loads((tmp/'manifests'/files[2].name).read_text())
        if d['document_id']!=m['document_id'] or any(x.get('document_id')!=d['document_id'] for x in c): raise ValueError('batch identity mismatch')
        for f in files: f.parent.mkdir(parents=True,exist_ok=True)
        for rel,f in zip(('documents/'+files[0].name,'chunks/'+files[1].name,'manifests/'+files[2].name),files): (tmp/rel).replace(f)
    finally:
        import shutil; shutil.rmtree(tmp,ignore_errors=True)

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--metadata',required=True); p.add_argument('--symbol',required=True); p.add_argument('--as-of',required=True); p.add_argument('--output-dir',required=True); p.add_argument('--overwrite',action='store_true'); a=p.parse_args(); root=Path('.local_data').resolve(); ip=safe(a.input,root); mp=safe(a.metadata,root)
 raw=ip.read_bytes(); meta=json.loads(mp.read_text(encoding='utf-8')); rel=str(ip.relative_to(root)); doc,chunks,man=build_sec_ingestion(raw,meta,a.symbol,a.as_of,input_file=rel,input_sha256=hashlib.sha256(raw).hexdigest())
 out=Path(a.output_dir).resolve()
 if root not in out.parents: raise ValueError('unsafe output path')
 out.mkdir(parents=True,exist_ok=True)
 did=doc['document_id']; files=[out/'documents'/f'{did}.json',out/'chunks'/f'{did}.jsonl',out/'manifests'/f'{did}.json']
 dp=json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2).encode(); cp=('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in chunks)+'\n').encode(); man.update(document_file=str(files[0].relative_to(root)),chunks_file=str(files[1].relative_to(root)),manifest_file=str(files[2].relative_to(root)),document_sha256=hashlib.sha256(dp).hexdigest(),chunks_sha256=hashlib.sha256(cp).hexdigest()); mpayload=json.dumps(man,ensure_ascii=False,sort_keys=True,indent=2).encode(); write_batch(files,[dp,cp,mpayload],a.overwrite)
 print(json.dumps({'document_id':did,'symbol':doc['symbol'],'form':doc['form'],'section_count':len(doc['sections']),'chunk_count':len(chunks),'network_executed':False,'model_calls':0}))
if __name__=='__main__':
 try: main()
 except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
