#!/usr/bin/env python3
import argparse,hashlib,json,os,sys
from pathlib import Path
from finsight_rag import build_sec_ingestion
def safe(p,root):
 p=Path(p); root=Path(root).resolve(); r=p.resolve()
 if p.is_symlink() or root not in r.parents or not p.is_file(): raise ValueError('unsafe input path')
 return p

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--metadata',required=True); p.add_argument('--symbol',required=True); p.add_argument('--as-of',required=True); p.add_argument('--output-dir',required=True); p.add_argument('--overwrite',action='store_true'); a=p.parse_args(); root=Path('.local_data').resolve(); ip=safe(a.input,root); mp=safe(a.metadata,root)
 raw=ip.read_bytes(); meta=json.loads(mp.read_text()); rel=str(ip.resolve().relative_to(root)); doc,chunks,man=build_sec_ingestion(raw,meta,a.symbol,a.as_of,input_file=rel,input_sha256=hashlib.sha256(raw).hexdigest()); out=Path(a.output_dir); outroot=root
 if out.resolve()!=outroot and outroot not in out.resolve().parents: raise ValueError('unsafe output path')
 out.mkdir(parents=True,exist_ok=True); base=out/'documents'; cb=out/'chunks'; mb=out/'manifests'; [x.mkdir(exist_ok=True) for x in (base,cb,mb)]; did=doc['document_id']; files=[base/f'{did}.json',cb/f'{did}.jsonl',mb/f'{did}.json']
 if any(x.exists() for x in files) and not a.overwrite: raise ValueError('output exists')
 docp=json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2).encode(); chunkp=('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in chunks)+'\n').encode(); man.update(document_file=str(files[0].relative_to(root)),chunks_file=str(files[1].relative_to(root)),manifest_file=str(files[2].relative_to(root)),document_sha256=hashlib.sha256(docp).hexdigest(),chunks_sha256=hashlib.sha256(chunkp).hexdigest()); manp=json.dumps(man,ensure_ascii=False,sort_keys=True,indent=2).encode()
 for f,data in zip(files,(docp,chunkp,manp)): tmp=f.with_name('.'+f.name+'.tmp'); tmp.write_bytes(data); os.replace(tmp,f)
 print(json.dumps({'document_id':did,'symbol':doc['symbol'],'form':doc['form'],'accession_number':doc['accession_number'],'section_count':len(doc['sections']),'chunk_count':len(chunks),'input_sha256':doc['input_sha256'],'document_sha256':man['document_sha256'],'chunks_sha256':man['chunks_sha256'],'network_executed':False,'model_calls':0}))
if __name__=='__main__':
 try: main()
 except Exception as e: print('error:',e,file=sys.stderr); raise SystemExit(2)
