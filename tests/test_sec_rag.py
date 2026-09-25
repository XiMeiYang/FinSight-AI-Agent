import hashlib, unittest
from pathlib import Path
from finsight_rag import clean_html, identify_sections, chunk_sections
class RagTests(unittest.TestCase):
 def test_clean_and_sections(self):
  t=clean_html(Path('tests/fixtures/sec_filing.synthetic.html').read_text()); self.assertNotIn('alert',t); self.assertIn('$10 million',t); secs=identify_sections(t); self.assertGreaterEqual(len(secs),1)
 def test_chunks_deterministic_and_hash(self):
  secs=identify_sections('Item 1 Business\n\n'+'x '*2000); a=chunk_sections(secs,target_chars=100,overlap_chars=20); b=chunk_sections(secs,target_chars=100,overlap_chars=20); self.assertEqual(a,b); self.assertTrue(all(x['text_sha256']==hashlib.sha256(x['text'].encode()).hexdigest() for x in a))
if __name__=='__main__': unittest.main()
