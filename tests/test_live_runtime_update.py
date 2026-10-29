import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('live_update', Path(__file__).parents[1] / 'tools/live_runtime_update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class RuntimeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.target, self.transaction = [self.root / x for x in ('source', 'target', 'transaction')]
        self.source.mkdir(); self.target.mkdir()
        (self.source / 'old.py').write_text('value = 2\n')
        (self.source / 'new.py').write_text('value = 3\n')
        (self.target / 'old.py').write_text('value = 1\n')
        (self.target / 'unrelated.txt').write_text('retain')
        update.stage(self.source, self.target, self.transaction, 'test-head')

    def test_apply_and_rollback_preserve_unrelated_files(self):
        update.transition(self.transaction, idle=lambda: None)
        self.assertEqual((self.target / 'old.py').read_text(), 'value = 2\n')
        update.transition(self.transaction, rollback=True, idle=lambda: None)
        self.assertEqual((self.target / 'old.py').read_text(), 'value = 1\n')
        self.assertFalse((self.target / 'new.py').exists())
        self.assertEqual((self.target / 'unrelated.txt').read_text(), 'retain')

    def test_live_target_drift_rejected_before_writes(self):
        (self.target / 'old.py').write_text('owner edit')
        with self.assertRaises(ValueError):
            update.transition(self.transaction, idle=lambda: None)
        self.assertEqual((self.target / 'old.py').read_text(), 'owner edit')
        self.assertFalse((self.target / 'new.py').exists())

    def test_candidate_tamper_rejected(self):
        (self.transaction / 'after/new.py').write_text('tampered')
        with self.assertRaises(ValueError):
            update.transition(self.transaction, idle=lambda: None)
        self.assertFalse((self.target / 'new.py').exists())

    def test_services_start_mid_update_restores_written_files(self):
        calls = 0
        def idle():
            nonlocal calls
            calls += 1
            if calls == 3:
                raise ValueError('services started')
        with self.assertRaises(ValueError):
            update.transition(self.transaction, idle=idle)
        self.assertFalse((self.target / 'new.py').exists())
        self.assertEqual((self.target / 'old.py').read_text(), 'value = 1\n')

    def test_unsafe_member_rejected(self):
        for name in ('../escape.py', 'C:/escape.py', 'x\\escape.py', '/escape.py'):
            with self.assertRaises(ValueError):
                update.member(self.target, name)


if __name__ == '__main__':
    unittest.main()
