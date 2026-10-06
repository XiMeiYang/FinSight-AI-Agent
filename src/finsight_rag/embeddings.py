"""Replaceable document/query embedding interfaces for local retrieval."""
from __future__ import annotations
from abc import ABC,abstractmethod
import importlib.metadata
from pathlib import Path
import numpy as np

BGE_QUERY_INSTRUCTION="Represent this sentence for searching relevant passages: "
class Embedder(ABC):
 model_name:str; model_revision:str; model_license:str; dimension:int; max_seq_length:int; normalization:bool; query_instruction:str; dependency_versions:dict
 @abstractmethod
 def encode_documents(self,texts): ...
 @abstractmethod
 def encode_queries(self,texts): ...
def checked_embeddings(value,dimension,expected_rows):
 matrix=np.asarray(value)
 if matrix.dtype!=np.float32 or matrix.shape!=(expected_rows,dimension) or not np.isfinite(matrix).all(): raise ValueError("invalid embedding matrix")
 if expected_rows and not np.allclose(np.linalg.norm(matrix,axis=1),1.0,rtol=1e-4,atol=1e-5): raise ValueError("embeddings must be normalized")
 return matrix
class FakeEmbedder(Embedder):
 model_name="synthetic-fake"; model_revision="synthetic-1"; model_license="synthetic"; max_seq_length=512; normalization=True; query_instruction="synthetic-query: "; dependency_versions={"numpy":np.__version__}
 def __init__(self,dimension=32): self.dimension=dimension; self.document_calls=0; self.query_calls=0; self.network_executed=False
 def _encode(self,texts,prefix):
  values=list(texts); output=np.zeros((len(values),self.dimension),dtype=np.float32)
  for i,text in enumerate(values):
   for token in (prefix+str(text)).lower().split(): output[i,int.from_bytes(token.encode()[:4].ljust(4,b'\0'),'little')%self.dimension]+=1
  norms=np.linalg.norm(output,axis=1,keepdims=True); output=np.divide(output,norms,out=np.zeros_like(output),where=norms!=0)
  return output
 def encode_documents(self,texts): self.document_calls+=1; values=list(texts); return checked_embeddings(self._encode(values,"document "),self.dimension,len(values))
 def encode_queries(self,texts): self.query_calls+=1; values=list(texts); return checked_embeddings(self._encode(values,"query "),self.dimension,len(values))
class BGEEmbedder(Embedder):
 model_license="MIT"; normalization=True; query_instruction=BGE_QUERY_INSTRUCTION
 def __init__(self,model_name="BAAI/bge-small-en-v1.5",revision=None,batch_size=32,cache_folder=".local_data/models/hub",*,local_files_only=False):
  if not revision: raise ValueError("model revision is required")
  if not isinstance(batch_size,int) or batch_size<=0: raise ValueError("batch_size must be positive")
  cache=Path(cache_folder).resolve()
  local_root=(Path.cwd()/".local_data/models").resolve()
  if not cache.is_relative_to(local_root): raise ValueError("model cache must be inside .local_data/models")
  try:
   from sentence_transformers import SentenceTransformer
  except ImportError as exc: raise RuntimeError("sentence-transformers is required") from exc
  self.model_name=model_name; self.model_revision=revision; self.batch_size=batch_size; self.network_executed=False if local_files_only else None
  self._model=SentenceTransformer(model_name,revision=revision,device="cpu",cache_folder=str(cache),local_files_only=local_files_only)
  getter=getattr(self._model,"get_embedding_dimension",self._model.get_sentence_embedding_dimension); self.dimension=int(getter()); self.max_seq_length=int(self._model.max_seq_length)
  packages=("sentence-transformers","transformers","huggingface-hub","torch","numpy"); self.dependency_versions={name:importlib.metadata.version(name) for name in packages}
 def _encode(self,texts):
  values=list(texts); result=self._model.encode(values,batch_size=self.batch_size,show_progress_bar=False,convert_to_numpy=True,normalize_embeddings=True,device="cpu",precision="float32")
  return checked_embeddings(result,self.dimension,len(values))
 def encode_documents(self,texts): return self._encode(texts)
 def encode_queries(self,texts): return self._encode([self.query_instruction+text for text in texts])
