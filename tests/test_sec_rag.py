import hashlib, unittest, json
from pathlib import Path
ROOT=Path('tests')
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

class ContractTests(unittest.TestCase):
    def test_bytes_hash_and_mismatch(self):
        from finsight_rag.ingestion import build_sec_ingestion
        meta=json.loads((ROOT/'fixtures/sec_filing_metadata.synthetic.json').read_text())
        raw=(ROOT/'fixtures/sec_filing.synthetic.html').read_bytes()
        doc,_,_=build_sec_ingestion(raw,meta,' TEST ','2024-12-31',input_sha256=__import__('hashlib').sha256(raw).hexdigest())
        self.assertEqual(doc['input_sha256'],__import__('hashlib').sha256(raw).hexdigest())
        with self.assertRaisesRegex(ValueError,'mismatch'): build_sec_ingestion(raw,meta,'TEST','2024-12-31',input_sha256='0'*64)
    def test_source_and_time_contract(self):
        from finsight_rag.ingestion import build_sec_ingestion
        meta=json.loads((ROOT/'fixtures/sec_filing_metadata.synthetic.json').read_text()); raw=(ROOT/'fixtures/sec_filing.synthetic.html').read_text()
        meta['source_url']='https://evil.example/x'
        with self.assertRaises(ValueError): build_sec_ingestion(raw,meta,'TEST','2024-12-31')
        meta['source_url']='https://www.sec.gov/Archives/x'; meta['accepted_at']='20241231170000'
        build_sec_ingestion(raw,meta,'TEST','2024-12-31')
        meta['accepted_at']='20250101170000'
        with self.assertRaises(ValueError): build_sec_ingestion(raw,meta,'TEST','2024-12-31')

if __name__=='__main__': unittest.main()
