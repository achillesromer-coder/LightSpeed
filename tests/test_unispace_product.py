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
