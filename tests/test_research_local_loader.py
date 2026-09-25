import json, tempfile, unittest
from pathlib import Path
from finsight_research.local_loader import load_json, atomic_write_json, LocalDataError
class LocalLoaderTests(unittest.TestCase):
 def setUp(self): self.t=tempfile.TemporaryDirectory(); self.root=Path(self.t.name)/'.local_data'; self.root.mkdir(); (self.root/'x.json').write_text('{"ok":true}')
 def tearDown(self): self.t.cleanup()
 def test_load_and_hash(self):
  value,meta=load_json('x.json',data_root=self.root); self.assertTrue(value['ok']); self.assertEqual(len(meta['sha256']),64)
 def test_traversal_missing_dir_invalid(self):
  for p in ('../x.json','none.json'):
   with self.assertRaises(LocalDataError): load_json(p,data_root=self.root)
  (self.root/'d').mkdir()
  with self.assertRaises(LocalDataError): load_json('d',data_root=self.root)
  (self.root/'bad.json').write_text('{')
  with self.assertRaises(LocalDataError): load_json('bad.json',data_root=self.root)
 def test_symlink_rejected(self):
  outside=Path(self.t.name)/'outside.json'; outside.write_text('{}')
  try: (self.root/'link.json').symlink_to(outside)
  except OSError: self.skipTest('symlink unavailable')
  with self.assertRaises(LocalDataError): load_json('link.json',data_root=self.root)
 def test_atomic_overwrite(self):
  rel,sha=atomic_write_json('out/a.json',{'x':1},data_root=self.root); self.assertEqual(rel,'out/a.json'); self.assertEqual(json.loads((self.root/rel).read_text()),{'x':1})
  with self.assertRaises(LocalDataError): atomic_write_json('out/a.json',{'x':2},data_root=self.root)
  atomic_write_json('out/a.json',{'x':2},data_root=self.root,overwrite=True); self.assertEqual(json.loads((self.root/rel).read_text()),{'x':2})
 def test_atomic_creates_isolated_missing_data_root(self):
  missing=Path(self.t.name)/'isolated'/'.local_data'
  rel,_=atomic_write_json('snapshots/a.json',{'ok':True},data_root=missing)
  self.assertEqual(rel,'snapshots/a.json')
  self.assertEqual(json.loads((missing/rel).read_text()),{'ok':True})
 def test_output_escape(self):
  with self.assertRaises(LocalDataError): atomic_write_json('../bad.json',{},data_root=self.root)
 def test_output_symlink_rejected_even_overwrite(self):
  target=self.root/'target.json'; target.write_text('{}')
  link=self.root/'link.json'
  try: link.symlink_to(target)
  except OSError: self.skipTest('symlink unavailable')
  with self.assertRaises(LocalDataError): atomic_write_json('link.json',{'x':1},data_root=self.root,overwrite=True)
if __name__=='__main__': unittest.main()
