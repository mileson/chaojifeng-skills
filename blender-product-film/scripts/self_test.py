"""Cheap contract/cache security tests; no downloads, Blender processes or user data changes."""
import copy,json,tempfile,unittest,zipfile
from pathlib import Path
from common import inside,sha256,validate_spec
from prepare_assets import safe_extract,fetch

class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_paths(self):
        for name in ['../escape','/absolute','C:\\escape','..\\escape']:
            with self.assertRaises(ValueError):inside(self.root,name)
        self.assertEqual(inside(self.root,'assets/a.png'),(self.root/'assets/a.png').resolve())
    def test_template_requires_product(self):
        s=json.loads((Path(__file__).resolve().parents[1]/'templates/scene.json').read_text())
        with self.assertRaises(ValueError):validate_spec(s)
        s['product']={k:'Test fact' for k in s['product']};validate_spec(s)
        broken=copy.deepcopy(s);broken['shots'][0]['end']-=1
        with self.assertRaises(ValueError):validate_spec(broken)
        s['requires_humans']=True
        with self.assertRaises(ValueError):validate_spec(s)
    def test_zip_traversal(self):
        archive=self.root/'bad.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape.txt','bad')
        with self.assertRaises(ValueError):safe_extract(archive,self.root/'unpacked')
        self.assertFalse((self.root/'escape.txt').exists())
    def test_local_cache_and_integrity(self):
        archive=self.root/'good.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('asset.txt','fixture')
        asset={'id':'test','local_path':str(archive),'sha256':sha256(archive),'license':'Self-authored fixture','license_source':'This test','license_verified':True,'extract':True}
        a=fetch(asset,self.root/'cache');b=fetch(asset,self.root/'cache');self.assertEqual(a,b)
        self.assertEqual((Path(a['directory'])/'asset.txt').read_text(),'fixture')
        bad=dict(asset,sha256='0'*64)
        with self.assertRaises(ValueError):fetch(bad,self.root/'cache')
        with self.assertRaises(ValueError):fetch(dict(asset,license_verified=False),self.root/'cache')

if __name__=='__main__':unittest.main()
