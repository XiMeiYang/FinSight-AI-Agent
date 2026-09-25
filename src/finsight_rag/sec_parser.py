import hashlib, html, re, unicodedata
from html.parser import HTMLParser
class _P(HTMLParser):
 def __init__(self): super().__init__(); self.out=[]; self.skip=0
 def handle_starttag(self,t,a): self.skip+=1 if t.lower() in {'script','style','noscript','nav','iframe'} else 0
 def handle_endtag(self,t): self.skip=max(0,self.skip-1) if t.lower() in {'script','style','noscript','nav','iframe'} else self.skip
 def handle_data(self,d):
  if not self.skip: self.out.append(d)
def clean_html(raw):
 p=_P(); p.feed(html.unescape(raw)); text='\n'.join(p.out); text=unicodedata.normalize('NFKC',text); text=re.sub(r'[ \t\f\r]+',' ',text); text=re.sub(r'\n\s*\n+','\n\n',text); return text.strip()
def identify_sections(text):
 pat=re.compile(r'(?im)^(?P<title>\s*(?:Item\s+\d+[A-Z]?\.?\s*[^\n]*|Management[’\']?s Discussion[^\n]*|Risk Factors|Financial Statements|Controls and Procedures)\s*)$')
 hits=[m for m in pat.finditer(text) if m.start()==0 or text[max(0,m.start()-80):m.start()].count('\n')>=1]
 sections=[]
 for i,m in enumerate(hits):
  start=m.start(); end=hits[i+1].start() if i+1<len(hits) else len(text); body=text[start:end].strip()
  if len(body)<len(m.group('title').strip())+2: continue
  title=m.group('title').strip(); sections.append({'section_id':f'section-{len(sections)+1:04d}','section_title':title,'section_order':len(sections)+1,'start_offset':start,'end_offset':end,'text':body,'text_sha256':hashlib.sha256(body.encode()).hexdigest()})
 if not sections: sections=[{'section_id':'UNSECTIONED','section_title':'UNSECTIONED','section_order':1,'start_offset':0,'end_offset':len(text),'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest()}]
 return sections
