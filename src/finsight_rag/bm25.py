"""Pure Python Okapi BM25."""
from __future__ import annotations
import math
from collections import Counter, defaultdict
class BM25Index:
    def __init__(self, documents: list[list[str]], *, k1: float=1.5, b: float=.75):
        if k1 < 0 or not 0 <= b <= 1: raise ValueError("invalid BM25 parameters")
        self.k1,self.b=k1,b; self.documents=documents; self.doc_lengths=[len(x) for x in documents]
        self.avgdl=sum(self.doc_lengths)/len(documents) if documents else 0.0
        self.df=Counter(); self.postings=defaultdict(dict)
        for i,tokens in enumerate(documents):
            counts=Counter(tokens)
            for t,tf in counts.items(): self.df[t]+=1; self.postings[t][i]=tf
    def score(self, query_tokens: list[str], doc_id: int) -> float:
        dl=self.doc_lengths[doc_id]; total=0.0
        for term in query_tokens:
            tf=self.postings.get(term,{}).get(doc_id,0)
            if not tf: continue
            df=self.df[term]; idf=math.log(1+(len(self.documents)-df+.5)/(df+.5))
            denom=tf+self.k1*(1-self.b+self.b*dl/(self.avgdl or 1))
            total += idf*(tf*(self.k1+1)/denom)
        return total
    def scores(self, query_tokens: list[str], candidates=None):
        ids=range(len(self.documents)) if candidates is None else candidates
        return {i:self.score(query_tokens,i) for i in ids}
