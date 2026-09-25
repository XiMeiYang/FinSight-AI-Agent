import hashlib, unittest, json
from pathlib import Path
from finsight_rag import clean_html, identify_sections, chunk_sections
class RagTests(unittest.TestCase):
 def test_clean_and_sections(self):
  t=clean_html(Path('tests/fixtures/sec_filing.synthetic.html').read_text()); self.assertNotIn('alert',t); self.assertIn('$10 million',t); secs=identify_sections(t); self.assertGreaterEqual(len(secs),1)
 def test_chunks_deterministic_and_hash(self):
  secs=identify_sections('Item 1 Business\n\n'+'x '*2000); a=chunk_sections(secs,target_chars=100,overlap_chars=20); b=chunk_sections(secs,target_chars=100,overlap_chars=20); self.assertEqual(a,b); self.assertTrue(all(x['text_sha256']==hashlib.sha256(x['text'].encode()).hexdigest() for x in a))
 def test_metadata_identity_and_outputs(self):
     from finsight_rag import build_sec_ingestion
     meta=json.loads(Path('tests/fixtures/sec_filing_metadata.synthetic.json').read_text()); raw=Path('tests/fixtures/sec_filing.synthetic.html').read_text(); d,c,m=build_sec_ingestion(raw,meta,' test ','2024-12-31',input_file='sec/raw/test.html')
     self.assertEqual(d['symbol'],'TEST'); self.assertTrue(d['cik']); self.assertTrue(d['accession_number']); self.assertTrue(c[0]['citation'].count('|')>=5); self.assertFalse(m['network_executed'])
     with self.assertRaises(ValueError): build_sec_ingestion(raw,meta,'NVDA','2024-12-31')
     with self.assertRaises(ValueError): build_sec_ingestion(raw,{**meta,'cik':'0'},'TEST','2024-12-31')
     with self.assertRaises(ValueError): build_sec_ingestion(raw,{**meta,'form':'S-8'},'TEST','2024-12-31')

if __name__=='__main__': unittest.main()
