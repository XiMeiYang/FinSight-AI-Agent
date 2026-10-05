"""Auditable, deterministic and fully offline SEC BM25 retrieval."""
from __future__ import annotations
import hashlib,json,os,re,shutil,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from .bm25 import BM25Index
from .ingestion import parse_time
from .tokenizer import TOKENIZER_VERSION,tokenize,validate_query

SCHEMA_VERSION="sec-bm25-index-1.0"
REQUIRED_FILES=("raw.bin","metadata.json","document.json","chunks.jsonl","ingestion-manifest.json")
_SYMBOL=re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$"); _CIK=re.compile(r"^\d{10}$"); _ACCESSION=re.compile(r"^\d{10}-\d{2}-\d{6}$"); _FORMS={"10-K","10-Q"}

def _json_bytes(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _read_json(path):
 value=json.loads(Path(path).read_text(encoding="utf-8"))
 if not isinstance(value,dict): raise ValueError("JSON object required")
 return value
def _local_data_path(path,must_exist=False):
 lexical=Path(path).absolute(); parts=lexical.parts
 if ".local_data" not in parts: raise ValueError("path must be inside .local_data")
 cursor=lexical
 while cursor!=cursor.parent:
  if cursor.exists() and cursor.is_symlink(): raise ValueError("symbolic links are not allowed")
  if cursor.name==".local_data": break
  cursor=cursor.parent
 root=Path(*parts[:parts.index(".local_data")+1]).resolve(strict=False); absolute=lexical.resolve(strict=False)
 if not absolute.is_relative_to(root): raise ValueError("path traversal outside .local_data")
 if must_exist and not absolute.exists(): raise ValueError("path does not exist")
 cursor=absolute
 while cursor!=cursor.parent:
  if cursor.exists() and cursor.is_symlink(): raise ValueError("symbolic links are not allowed")
  if cursor.name==".local_data": break
  cursor=cursor.parent
 if cursor.name!=".local_data": raise ValueError("invalid .local_data path")
 return absolute
def _sec_archive_url(value):
 if not isinstance(value,str): raise ValueError("missing SEC source URL")
 p=urlparse(value)
 if p.scheme!="https" or p.hostname!="www.sec.gov" or p.port not in (None,443) or p.username or p.password or not p.path.startswith("/Archives/"): raise ValueError("invalid SEC source URL")
 return value
def _identity(obj): return tuple(str(obj.get(k,"")) for k in ("symbol","cik","form","accession_number","document_id"))
def _validate_identity(identity):
 symbol,cik,form,accession,document_id=identity
 if not _SYMBOL.fullmatch(symbol) or not _CIK.fullmatch(cik) or form not in _FORMS or not _ACCESSION.fullmatch(accession) or not document_id: raise ValueError("invalid filing identity")

def _validate_bundle(bundle,corpus):
 if bundle.is_symlink() or not bundle.is_dir(): raise ValueError("invalid bundle")
 files={name:bundle/name for name in REQUIRED_FILES}
 if any(not p.is_file() or p.is_symlink() for p in files.values()): raise ValueError("incomplete bundle")
 metadata=_read_json(files["metadata.json"]); document=_read_json(files["document.json"]); manifest=_read_json(files["ingestion-manifest.json"])
 identity=_identity(metadata); _validate_identity(identity)
 if _identity(document)!=identity or _identity(manifest)!=identity: raise ValueError("bundle identity conflict")
 if bundle.parts[-3]!=identity[0] or bundle.name!=identity[3].replace("-",""): raise ValueError("bundle path identity conflict")
 expected={"raw.bin":(metadata.get("raw_sha256"),manifest.get("raw_sha256"),document.get("input_sha256")),"metadata.json":(manifest.get("metadata_sha256"),),"document.json":(manifest.get("document_sha256"),),"chunks.jsonl":(manifest.get("chunks_sha256"),)}
 for name,values in expected.items():
  digest=_sha256(files[name])
  if any(value!=digest for value in values): raise ValueError(f"{name} hash mismatch")
 source=_sec_archive_url(metadata.get("source_url")); as_of=document.get("as_of") or manifest.get("as_of"); cutoff=parse_time(as_of,date_only_end=True)
 for key in ("accepted_at","published_at"):
  if metadata.get(key) and parse_time(metadata[key])>cutoff: raise ValueError("filing after corpus as_of")
 chunks=[]; seen=set()
 for line in files["chunks.jsonl"].read_text(encoding="utf-8").splitlines():
  if not line.strip(): continue
  chunk=json.loads(line); cid=chunk.get("chunk_id")
  if not isinstance(chunk,dict) or _identity(chunk)!=identity: raise ValueError("chunk identity conflict")
  if not isinstance(cid,str) or not cid or cid in seen: raise ValueError("duplicate or invalid chunk ID")
  seen.add(cid)
  if not isinstance(chunk.get("text"),str) or not chunk["text"].strip() or hashlib.sha256(chunk["text"].encode()).hexdigest()!=chunk.get("text_sha256"): raise ValueError("invalid chunk text")
  if _sec_archive_url(chunk.get("source_url"))!=source: raise ValueError("chunk source conflict")
  citation=chunk.get("citation"); required=(identity[0],identity[2],identity[3],str(chunk.get("section_title","")),f'| chunk {chunk.get("chunk_index")} |',source)
  if not isinstance(citation,str) or any(value not in citation for value in required): raise ValueError("invalid chunk citation")
  chunks.append(chunk)
 if len(chunks)!=manifest.get("chunk_count") or len(document.get("sections",[]))!=manifest.get("section_count"): raise ValueError("bundle count mismatch")
 return chunks,{"symbol":identity[0],"accession_number":identity[3],"relative_path":bundle.relative_to(corpus).as_posix(),"files":{name:_sha256(path) for name,path in files.items()},"as_of":as_of}

def load_corpus(corpus):
 corpus=_local_data_path(corpus,True)
 if not corpus.is_dir() or corpus.is_symlink(): raise ValueError("invalid corpus path")
 paths=sorted(p for p in corpus.glob("*/filings/*") if not p.name.startswith("."))
 if not paths: raise ValueError("corpus has no bundles")
 docs=[]; bundles=[]; seen=set()
 for path in paths:
  rows,info=_validate_bundle(path,corpus)
  for row in rows:
   if row["chunk_id"] in seen: raise ValueError("duplicate chunk ID across corpus")
   seen.add(row["chunk_id"]); docs.append(row)
  bundles.append(info)
 aggregate=[{"ticker":x["symbol"],"accession":x["accession_number"],"files":x["files"]} for x in bundles]; aggregate.sort(key=lambda x:(x["ticker"],x["accession"]))
 return docs,bundles,hashlib.sha256(_json_bytes(aggregate)).hexdigest()

def _company_catalog(corpus,bundles):
 candidates=sorted(corpus.glob("semiconductor-candidates-*.json"))
 if len(candidates)!=1 or candidates[0].is_symlink(): raise ValueError("one local candidate manifest is required for company names")
 payload=_read_json(candidates[0]); names={}
 bundle_identity={(x["symbol"],x["accession_number"]) for x in bundles}
 for company in payload.get("candidates",[]):
  symbol=company.get("ticker"); name=company.get("company_name"); cik=str(company.get("cik",""))
  if not _SYMBOL.fullmatch(str(symbol)) or not isinstance(name,str) or not name.strip() or not _CIK.fullmatch(cik): raise ValueError("invalid company catalog")
  names[symbol]=(name.strip(),cik)
 for symbol,_ in bundle_identity:
  if symbol not in names: raise ValueError("company name missing from catalog")
 return names,candidates[0]

_INDEX_KEYS=("chunk_id","document_id","symbol","cik","form","accession_number","filing_date","accepted_at","published_at","source_url","section_id","section_title","chunk_index","text")
def _content_digest(rows): return hashlib.sha256(_json_bytes([{k:row.get(k) for k in _INDEX_KEYS} for row in rows])).hexdigest()
def _indexed_digest(rows): return hashlib.sha256(_json_bytes([{k:row.get(k) for k in _INDEX_KEYS+("company_name","corpus_as_of")} for row in rows])).hexdigest()

def _manifest_hash(manifest): return hashlib.sha256(_json_bytes({k:v for k,v in manifest.items() if k!="index_sha256"})).hexdigest()
def _validate_index_files(path,manifest):
 for name,key in (("documents.jsonl","documents_sha256"),("postings.json","postings_sha256")):
  p=path/name
  if not p.is_file() or p.is_symlink() or _sha256(p)!=manifest.get(key): raise ValueError("index artifact hash mismatch")
 if manifest.get("index_sha256")!=_manifest_hash(manifest): raise ValueError("index manifest hash mismatch")

def build_index(corpus,output,*,overwrite=False,k1=1.5,b=.75):
 if k1<=0 or not 0<=b<=1: raise ValueError("invalid BM25 parameters")
 corpus=_local_data_path(corpus,True); output=_local_data_path(output)
 docs,bundles,corpus_digest=load_corpus(corpus); companies,catalog_path=_company_catalog(corpus,bundles); payload=[]; per_company=Counter(); per_form=Counter()
 as_of_by_accession={x["accession_number"]:x["as_of"] for x in bundles}
 for chunk in docs:
  row={key:chunk.get(key) for key in _INDEX_KEYS}
  company_name,company_cik=companies[chunk["symbol"]]
  if company_cik!=chunk["cik"]: raise ValueError("company catalog CIK conflict")
  row["company_name"]=company_name; row["corpus_as_of"]=as_of_by_accession[chunk["accession_number"]]; payload.append(row); per_company[row["symbol"]]+=1; per_form[row["form"]]+=1
 tokenized=[tokenize(x["text"]) for x in payload]; bm25=BM25Index(tokenized,k1=k1,b=b)
 catalog_digest=_sha256(catalog_path); index_id=hashlib.sha256(_json_bytes({"corpus":corpus_digest,"catalog":catalog_digest,"tokenizer":TOKENIZER_VERSION,"k1":k1,"b":b})).hexdigest()[:24]
 try: corpus_relative=corpus.relative_to(Path.cwd().absolute()).as_posix()
 except ValueError: corpus_relative=corpus.name
 manifest={"schema_version":SCHEMA_VERSION,"index_id":index_id,"created_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"corpus_aggregate_sha256":corpus_digest,"corpus_chunks_sha256":_content_digest(docs),"indexed_documents_sha256":_indexed_digest(payload),"corpus_relative_path":corpus_relative,"company_catalog_relative_path":catalog_path.relative_to(corpus).as_posix(),"company_catalog_sha256":catalog_digest,"tokenizer_version":TOKENIZER_VERSION,"bm25":{"k1":k1,"b":b,"idf":"log(1+(N-df+0.5)/(df+0.5))"},"document_count":len({x["document_id"] for x in payload}),"chunk_count":len(payload),"vocabulary_size":len(bm25.df),"average_document_length":bm25.avgdl,"chunks_per_company":dict(sorted(per_company.items())),"chunks_per_form":dict(sorted(per_form.items())),"input_bundles":[x["relative_path"] for x in bundles],"network_executed":False,"model_calls":0,"status":"completed"}
 if output.exists():
  if output.is_symlink() or not output.is_dir(): raise ValueError("invalid existing index")
  if not overwrite:
   try: old=_read_json(output/"manifest.json"); _validate_index_files(output,old)
   except Exception as exc: raise FileExistsError("existing index is incomplete or invalid") from exc
   keys=("schema_version","index_id","corpus_aggregate_sha256","corpus_chunks_sha256","indexed_documents_sha256","company_catalog_sha256","tokenizer_version","bm25")
   if all(old.get(k)==manifest.get(k) for k in keys): result=dict(old); result["status"]="already_completed"; return result
   raise FileExistsError("conflicting index already exists")
 output.parent.mkdir(parents=True,exist_ok=True); temp=Path(tempfile.mkdtemp(prefix=f".{output.name}.batch-",dir=output.parent)); backup=output.parent/f".{output.name}.backup"
 try:
  (temp/"documents.jsonl").write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n" for x in payload),encoding="utf-8")
  postings={term:{str(doc):tf for doc,tf in sorted(entries.items())} for term,entries in sorted(bm25.postings.items())}; (temp/"postings.json").write_text(json.dumps(postings,sort_keys=True,separators=(",",":")),encoding="utf-8")
  manifest["documents_sha256"]=_sha256(temp/"documents.jsonl"); manifest["postings_sha256"]=_sha256(temp/"postings.json"); manifest["index_sha256"]=_manifest_hash(manifest); (temp/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8"); _validate_index_files(temp,manifest)
  if output.exists():
   if backup.exists(): raise ValueError("stale index backup exists")
   os.replace(output,backup)
   try: os.replace(temp,output)
   except Exception: os.replace(backup,output); raise
   shutil.rmtree(backup)
  else: os.replace(temp,output)
 except Exception:
  shutil.rmtree(temp,ignore_errors=True)
  if backup.exists() and not output.exists(): os.replace(backup,output)
  raise
 return manifest

def load_index(path,corpus=None):
 path=_local_data_path(path,True)
 if not path.is_dir() or path.is_symlink(): raise ValueError("invalid index path")
 manifest=_read_json(path/"manifest.json")
 if manifest.get("schema_version")!=SCHEMA_VERSION or manifest.get("tokenizer_version")!=TOKENIZER_VERSION: raise ValueError("incompatible index schema")
 _validate_index_files(path,manifest); docs=[json.loads(x) for x in (path/"documents.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
 if len(docs)!=manifest.get("chunk_count"): raise ValueError("index document count mismatch")
 if corpus is None:
  candidate=Path(manifest.get("corpus_relative_path","")); corpus=candidate if candidate.is_absolute() else Path.cwd()/candidate
 corpus_docs,bundles,digest=load_corpus(corpus)
 if digest!=manifest.get("corpus_aggregate_sha256"): raise ValueError("index corpus provenance mismatch")
 if _content_digest(corpus_docs)!=manifest.get("corpus_chunks_sha256") or _content_digest(docs)!=manifest.get("corpus_chunks_sha256"): raise ValueError("index content provenance mismatch")
 catalog=Path(corpus)/manifest.get("company_catalog_relative_path","")
 if not catalog.is_file() or catalog.is_symlink() or _sha256(catalog)!=manifest.get("company_catalog_sha256"): raise ValueError("company catalog provenance mismatch")
 companies,_=_company_catalog(Path(corpus),bundles); as_of={x["accession_number"]:x["as_of"] for x in bundles}
 for row in docs:
  if row.get("company_name")!=companies[row["symbol"]][0] or row.get("corpus_as_of")!=as_of[row["accession_number"]]: raise ValueError("derived index provenance mismatch")
 if _indexed_digest(docs)!=manifest.get("indexed_documents_sha256"): raise ValueError("indexed document provenance mismatch")
 bm25=BM25Index([tokenize(x["text"]) for x in docs],k1=manifest["bm25"]["k1"],b=manifest["bm25"]["b"])
 postings=json.loads((path/"postings.json").read_text(encoding="utf-8")); expected={term:{str(doc):tf for doc,tf in sorted(entries.items())} for term,entries in sorted(bm25.postings.items())}
 if postings!=expected: raise ValueError("postings content mismatch")
 return manifest,docs,bm25

def search_loaded(manifest,docs,bm25,query,*,top_k=10,symbol=None,form=None,as_of=None):
 if not isinstance(top_k,int) or not 1<=top_k<=50: raise ValueError("top_k must be between 1 and 50")
 tokens=validate_query(query); known={x["symbol"] for x in docs}
 if symbol is not None:
  symbol=symbol.strip().upper()
  if symbol not in known: raise ValueError("unknown symbol")
 if form is not None:
  form=form.strip().upper()
  if form not in _FORMS: raise ValueError("invalid form")
 cutoff=parse_time(as_of,date_only_end=True) if as_of else None; candidates=[]
 for i,row in enumerate(docs):
  if symbol and row["symbol"]!=symbol: continue
  if form and row["form"]!=form: continue
  available=row.get("accepted_at") or row.get("published_at") or row.get("filing_date")
  if cutoff and (not available or parse_time(available)>cutoff): continue
  candidates.append(i)
 scores=bm25.scores(tokens,candidates); ranked=[i for i in candidates if scores[i]>0]; ranked.sort(key=lambda i:(-scores[i],docs[i]["symbol"],docs[i]["accession_number"],docs[i].get("section_id") or "",docs[i].get("chunk_index",0),docs[i]["chunk_id"]))
 results=[]
 for rank,i in enumerate(ranked[:top_k],1):
  row=docs[i]; results.append({"rank":rank,"score":scores[i],"symbol":row["symbol"],"company_name":row.get("company_name") or row["symbol"],"cik":row["cik"],"form":row["form"],"accession_number":row["accession_number"],"filing_date":row.get("filing_date"),"accepted_at":row.get("accepted_at"),"published_at":row.get("published_at"),"section":row.get("section_title"),"chunk_id":row["chunk_id"],"chunk_index":row.get("chunk_index"),"source_url":row.get("source_url"),"corpus_as_of":row.get("corpus_as_of"),"evidence_preview":row["text"][:400]})
 return results

def search(path,query,*,top_k=10,symbol=None,form=None,as_of=None,corpus=None):
 manifest,docs,bm25=load_index(path,corpus)
 return search_loaded(manifest,docs,bm25,query,top_k=top_k,symbol=symbol,form=form,as_of=as_of)
