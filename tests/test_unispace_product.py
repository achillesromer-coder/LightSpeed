import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('product_verifier', ROOT / 'tools/verify_unispace_product.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProductTests(unittest.TestCase):
    def fixture(self, folder, name='source.txt', wrong_hash=False):
        raw = b'reference'
        entry = {'path': name, 'size_bytes': len(raw), 'sha256': '0' * 64 if wrong_hash else hashlib.sha256(raw).hexdigest()}
        with zipfile.ZipFile(folder / 'CGX.cgx', 'w') as z:
            z.writestr(name, raw)
            z.writestr('cgx/bootstrap.json', json.dumps({'state_id': 'TEST'}))
            z.writestr('cgx/manifest.json', json.dumps({'state_id': 'TEST', 'files': [entry]}))
        data = (folder / 'CGX.cgx').read_bytes()
        contract = {'carrier': 'CGX.cgx', 'state_id': 'TEST', 'tracked_files': 1,
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        (folder / 'product.json').write_text(json.dumps(contract), encoding='utf-8')

    def test_published_snapshot(self):
        self.assertEqual(module.verify(ROOT / 'UniSpace')['tracked_files'], 432)

    def test_changed_outer_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            with (p / 'CGX.cgx').open('ab') as f: f.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'hash or size'): module.verify(p)

    def test_unsafe_member_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p, name='../escape')
            with self.assertRaisesRegex(ValueError, 'Unsafe'): module.verify(p)

    def test_manifest_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p, wrong_hash=True)
            with self.assertRaisesRegex(ValueError, 'Tracked member hash'): module.verify(p)

    def test_synthetic_valid_archive(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            self.assertFalse(module.verify(p)['embedded_code_executed'])


class NestedReferenceTests(unittest.TestCase):
    def test_nested(self):
        import io
        files={'a/x':b'x','a/b/y':b'y','z':b'x'}
        e=[dict(path=k,size_bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in files.items()]
        t=[dict(x,bytes=x['size_bytes'],semantic_path=['synthetic'],cell=x['path']) for x in e]
        root=module.nested_reference_index(e,t)
        self.assertEqual(root,module.nested_reference_index(e[::-1],t[::-1]))
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            for k,v in files.items(): z.writestr(k,v)
        with zipfile.ZipFile(b) as z:
            self.assertEqual(module.hydrate_nested(z,root,(),allowed_paths=set(files),max_bytes=3),files)
            self.assertEqual(module.hydrate_nested(z,root,('a','b'),allowed_paths={'a/b/y'},max_bytes=1),{'a/b/y':b'y'})
            with self.assertRaises(PermissionError): module.hydrate_nested(z,root,('a',),allowed_paths={'a/x'},max_bytes=3)
            with self.assertRaises(ValueError): module.hydrate_nested(z,root,(),allowed_paths=set(files),max_bytes=2)
    def test_synthetic_grammar(self):
        r=[(1,None,2),(1,2,3),(1,2,4),(4,2,1),(1,3,None)]; v={1,2,3,4}
        self.assertEqual(module.facet_transition_options(r,v,parent=1,neighbor=2),(3,4))
        self.assertEqual(module.facet_transition_options(r,v,parent=1,neighbor=3,direction='previous'),(2,))
        self.assertEqual(module.facet_transition_options(r,v,parent=4,neighbor=2),(1,))
        with self.assertRaises(ValueError): module.facet_transition_options(r,v|{174},parent=1,neighbor=2)
