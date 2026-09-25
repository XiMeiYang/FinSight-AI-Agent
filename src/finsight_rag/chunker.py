import hashlib

def chunk_sections(sections, *, target_chars=2000, overlap_chars=250, version='char-v1'):
 out=[]
 for sec in sections:
  text=sec['text']; pos=0; idx=0
  while pos<len(text):
   end=min(len(text),pos+target_chars)
   if end<len(text):
    cut=text.rfind('\n\n',pos,end)
    if cut>pos+target_chars//2: end=cut
   piece=text[pos:end].strip()
   if piece:
    cid=hashlib.sha256(f"{sec['section_id']}|{idx}|{piece}".encode()).hexdigest()[:20]
    out.append({'schema_version':'1.0','chunk_id':cid,'document_id':'','symbol':'','cik':'','accession_number':'','form':'','filing_date':None,'accepted_at':None,'source_url':None,'section_id':sec['section_id'],'section_title':sec['section_title'],'chunk_index':idx,'text':piece,'character_count':len(piece),'text_sha256':hashlib.sha256(piece.encode()).hexdigest(),'citation':''})
   if end>=len(text): break
   pos=max(end-overlap_chars,pos+1); idx+=1
 return out
