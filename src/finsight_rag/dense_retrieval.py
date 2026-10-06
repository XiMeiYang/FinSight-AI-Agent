"""Safe, auditable, in-memory dense retrieval for the local SEC corpus."""
from __future__ import annotations
import hashlib,json,os,shutil,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .ingestion import parse_time
from .retrieval import (_INDEX_KEYS,_company_catalog,_content_digest,_indexed_digest,
                        _local_data_path,_sha256,load_corpus)

SCHEMA_VERSION="sec-dense-index-1.0"
ARTIFACTS=("manifest.json","documents.jsonl","embeddings.npy")
def _canon(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def _manifest_hash(value): return hashlib.sha256(_canon({k:v for k,v in value.items() if k!="manifest_sha256"})).hexdigest()
def _validate_top_k(value):
 if not isinstance(value,int) or not 1<=value<=50: raise ValueError("top_k must be between 1 and 50")
def _normalized(matrix):
 return matrix.ndim==2 and np.isfinite(matrix).all() and np.allclose(np.linalg.norm(matrix,axis=1),1.0,rtol=1e-4,atol=1e-5)
def _rows(corpus,docs,bundles):
 companies,catalog=_company_catalog(corpus,bundles); as_of={x["accession_number"]:x["as_of"] for x in bundles}; rows=[]
 for chunk in docs:
  name,cik=companies[chunk["symbol"]]
  if cik!=chunk["cik"]: raise ValueError("company catalog CIK conflict")
  row={key:chunk.get(key) for key in _INDEX_KEYS}; row["company_name"]=name; row["corpus_as_of"]=as_of[chunk["accession_number"]]; rows.append(row)
 return rows,catalog
def _manifest_bytes(payload): return (json.dumps(payload,sort_keys=True,indent=2)+"\n").encode()
def _finish_size(payload,documents_size,embeddings_size):
 payload["index_size_bytes"]=0
 for _ in range(5):
  payload["manifest_sha256"]=_manifest_hash(payload); size=documents_size+embeddings_size+len(_manifest_bytes(payload))
  if size==payload["index_size_bytes"]: break
  payload["index_size_bytes"]=size
 payload["manifest_sha256"]=_manifest_hash(payload)

def build_dense_index(corpus,output,embedder,*,batch_size=32,overwrite=False):
 if not isinstance(batch_size,int) or batch_size<=0: raise ValueError("batch_size must be positive")
 if getattr(embedder,"network_executed",None) is not False: raise ValueError("offline embedder is required")
 corpus=_local_data_path(corpus,True); output=_local_data_path(output); docs,bundles,corpus_sha=load_corpus(corpus); rows,catalog=_rows(corpus,docs,bundles)
 texts=[row["text"] for row in rows]; start=time.perf_counter(); parts=[]
 for offset in range(0,len(texts),batch_size): parts.append(embedder.encode_documents(texts[offset:offset+batch_size]))
 matrix=np.vstack(parts) if parts else np.empty((0,embedder.dimension),dtype=np.float32)
 if matrix.dtype!=np.float32 or matrix.shape!=(len(rows),embedder.dimension) or not _normalized(matrix): raise ValueError("invalid normalized embedding matrix")
 catalog_sha=_sha256(catalog); index_id=hashlib.sha256(_canon({"corpus":corpus_sha,"chunks":_content_digest(docs),"catalog":catalog_sha,"model":embedder.model_name,"revision":embedder.model_revision,"dimension":embedder.dimension,"batch_size":batch_size})).hexdigest()[:24]
 payload={"schema_version":SCHEMA_VERSION,"index_id":index_id,"created_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"corpus_aggregate_sha256":corpus_sha,"corpus_chunks_sha256":_content_digest(docs),"indexed_documents_sha256":_indexed_digest(rows),"corpus_relative_path":corpus.relative_to(Path.cwd().resolve()).as_posix() if corpus.is_relative_to(Path.cwd().resolve()) else corpus.name,"company_catalog_relative_path":catalog.relative_to(corpus).as_posix(),"company_catalog_sha256":catalog_sha,"input_bundles":[x["relative_path"] for x in bundles],"model_name":embedder.model_name,"model_revision":embedder.model_revision,"model_license":embedder.model_license,"dimension":embedder.dimension,"max_seq_length":embedder.max_seq_length,"normalization":bool(embedder.normalization),"query_instruction":embedder.query_instruction,"batch_size":batch_size,"embedding_batch_count":len(parts),"text_count":len(texts),"document_count":len({r["document_id"] for r in rows}),"chunk_count":len(rows),"device":"cpu","dtype":"float32","dependency_versions":dict(sorted(embedder.dependency_versions.items())),"build_seconds":time.perf_counter()-start,"network_executed":embedder.network_executed,"llm_calls":0,"status":"completed"}
 if output.exists():
  if output.is_symlink() or not output.is_dir(): raise ValueError("invalid existing index")
  if not overwrite:
   try: old,_,_=load_dense_index(output,corpus,embedder)
   except Exception as exc: raise FileExistsError("existing dense index is incomplete or conflicting") from exc
   keys=("schema_version","index_id","corpus_aggregate_sha256","corpus_chunks_sha256","indexed_documents_sha256","company_catalog_sha256","model_name","model_revision","dimension","normalization","batch_size")
   if all(old.get(k)==payload.get(k) for k in keys): result=dict(old); result["status"]="already_completed"; return result
   raise FileExistsError("conflicting dense index exists")
 output.parent.mkdir(parents=True,exist_ok=True); temp=Path(tempfile.mkdtemp(prefix=f".{output.name}.batch-",dir=output.parent)); backup=output.parent/f".{output.name}.backup"
 try:
  documents=temp/"documents.jsonl"; embeddings=temp/"embeddings.npy"
  documents.write_text("".join(json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n" for row in rows),encoding="utf-8"); np.save(embeddings,matrix,allow_pickle=False)
  payload["documents_sha256"]=_sha256(documents); payload["embeddings_sha256"]=_sha256(embeddings); _finish_size(payload,documents.stat().st_size,embeddings.stat().st_size); (temp/"manifest.json").write_bytes(_manifest_bytes(payload))
  load_dense_index(temp,corpus,embedder)
  if output.exists():
   if backup.exists(): raise ValueError("stale dense index backup")
   os.replace(output,backup)
   try: os.replace(temp,output)
   except Exception: os.replace(backup,output); raise
   shutil.rmtree(backup)
  else: os.replace(temp,output)
 except Exception:
  shutil.rmtree(temp,ignore_errors=True)
  if backup.exists() and not output.exists(): os.replace(backup,output)
  raise
 return payload

def load_dense_index(index,corpus,embedder):
 index=_local_data_path(index,True); corpus=_local_data_path(corpus,True)
 if not index.is_dir() or index.is_symlink(): raise ValueError("invalid dense index")
 if any(not (index/name).is_file() or (index/name).is_symlink() for name in ARTIFACTS): raise ValueError("incomplete dense index")
 manifest=json.loads((index/"manifest.json").read_text(encoding="utf-8"))
 if manifest.get("schema_version")!=SCHEMA_VERSION or manifest.get("manifest_sha256")!=_manifest_hash(manifest): raise ValueError("invalid dense manifest")
 if manifest.get("model_name")!=embedder.model_name or manifest.get("model_revision")!=embedder.model_revision or manifest.get("dimension")!=embedder.dimension or manifest.get("normalization") is not True: raise ValueError("model provenance mismatch")
 documents=index/"documents.jsonl"; embeddings=index/"embeddings.npy"
 if _sha256(documents)!=manifest.get("documents_sha256") or _sha256(embeddings)!=manifest.get("embeddings_sha256"): raise ValueError("dense artifact hash mismatch")
 rows=[json.loads(line) for line in documents.read_text(encoding="utf-8").splitlines() if line.strip()]
 try: matrix=np.load(embeddings,allow_pickle=False)
 except Exception as exc: raise ValueError("invalid embedding file") from exc
 if matrix.dtype!=np.float32 or matrix.shape!=(len(rows),manifest.get("dimension")) or len(rows)!=manifest.get("chunk_count") or not _normalized(matrix): raise ValueError("invalid embedding shape, dtype, values or normalization")
 corpus_docs,bundles,corpus_sha=load_corpus(corpus); expected,catalog=_rows(corpus,corpus_docs,bundles)
 if corpus_sha!=manifest.get("corpus_aggregate_sha256") or _content_digest(corpus_docs)!=manifest.get("corpus_chunks_sha256"): raise ValueError("corpus provenance mismatch")
 if _sha256(catalog)!=manifest.get("company_catalog_sha256") or rows!=expected or _indexed_digest(rows)!=manifest.get("indexed_documents_sha256"): raise ValueError("dense row provenance mismatch")
 actual_size=sum((index/name).stat().st_size for name in ARTIFACTS)
 if actual_size!=manifest.get("index_size_bytes"): raise ValueError("dense index size mismatch")
 return manifest,rows,matrix

def search_loaded_dense(manifest,rows,matrix,query,embedder,*,top_k=10,symbol=None,form=None,as_of=None):
 if getattr(embedder,"network_executed",None) is not False: raise ValueError("offline embedder is required")
 _validate_top_k(top_k)
 if not isinstance(query,str) or not query.strip() or len(query)>2000: raise ValueError("invalid query")
 known={row["symbol"] for row in rows}
 if symbol is not None:
  symbol=symbol.strip().upper()
  if symbol not in known: raise ValueError("unknown symbol")
 if form is not None:
  form=form.strip().upper()
  if form not in {"10-K","10-Q"}: raise ValueError("invalid form")
 cutoff=parse_time(as_of,date_only_end=True) if as_of else None; candidates=[]
 for i,row in enumerate(rows):
  if symbol and row["symbol"]!=symbol: continue
  if form and row["form"]!=form: continue
  available=row.get("accepted_at") or row.get("published_at") or row.get("filing_date")
  if cutoff and (not available or parse_time(available)>cutoff): continue
  candidates.append(i)
 query_vector=embedder.encode_queries([query])
 if query_vector.dtype!=np.float32 or query_vector.shape!=(1,manifest["dimension"]) or not _normalized(query_vector): raise ValueError("invalid query embedding")
 scores=matrix[candidates]@query_vector[0] if candidates else np.empty((0,),dtype=np.float32); ranked=list(zip(candidates,scores.tolist())); ranked.sort(key=lambda item:(-item[1],rows[item[0]]["symbol"],rows[item[0]]["accession_number"],rows[item[0]].get("section_id") or "",rows[item[0]].get("chunk_index",0),rows[item[0]]["chunk_id"]))
 results=[]
 for rank,(i,score) in enumerate(ranked[:top_k],1):
  row=rows[i]; results.append({"rank":rank,"score":float(score),"symbol":row["symbol"],"company_name":row["company_name"],"cik":row["cik"],"form":row["form"],"accession_number":row["accession_number"],"filing_date":row.get("filing_date"),"accepted_at":row.get("accepted_at"),"published_at":row.get("published_at"),"section":row.get("section_title"),"chunk_id":row["chunk_id"],"chunk_index":row.get("chunk_index"),"source_url":row.get("source_url"),"corpus_as_of":row.get("corpus_as_of"),"evidence_preview":row["text"][:400]})
 return results

def search_dense(index,corpus,query,embedder,**kwargs):
 manifest,rows,matrix=load_dense_index(index,corpus,embedder); return search_loaded_dense(manifest,rows,matrix,query,embedder,**kwargs)
