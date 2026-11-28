import importlib.util
import json
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

# Run against the existing LOAD adapter, not a second implementation.
import manual_intake_review as intake

class ManualIntakeTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"intake"
        self.load=Path(self.tmp.name)/"load"
        self.root.mkdir()
        self.load.mkdir()
        (self.load/"R0_PACKS_private").mkdir()
        (self.load/"Local_batch_receipts").mkdir()
        (self.load/"INTEGRITY_AND_GC_GATES.review.json").write_text('{"schema":"CGX-LOAD-INTAKE-AUDIT/0.17"}',encoding="utf-8")
    def source(self,name,raw):
        p=self.root/name
        p.write_bytes(raw)
        return p
    def receipts(self):
        return list((self.load/"Local_batch_receipts").glob("*.review.json"))
    def test_recovery_and_replay(self):
        raw=b"# Test\nPreserve CRLF\r\n"
        p=self.source("a.md",raw)
        a=intake.ingest(self.root,self.load,p.name)
        b=intake.ingest(self.root,self.load,p.name)
        self.assertTrue(a["new_carrier"])
        self.assertFalse(b["new_carrier"])
        self.assertEqual(a["receipt_sha256"],b["receipt_sha256"])
        self.assertEqual(len(self.receipts()),1)
        self.assertEqual(p.read_bytes(),raw)
        pack=(self.load/"R0_PACKS_private"/(a["sha256"]+".cgxpre")).read_bytes()
        self.assertEqual(intake.restore(pack,a["sha256"]),raw)
        self.assertEqual(zlib.decompress(pack[49:]),raw)
    def test_same_bytes_distinct_occurrences(self):
        raw=b"# Fixture"
        self.source("a.md",raw)
        self.source("b.md",raw)
        a=intake.ingest(self.root,self.load,"a.md")
        b=intake.ingest(self.root,self.load,"b.md")
        self.assertNotEqual(a["occurrence"],b["occurrence"])
        self.assertEqual(a["sha256"],b["sha256"])
        self.assertEqual(len(self.receipts()),2)
        self.assertEqual(len(list((self.load/"R0_PACKS_private").glob("*.cgxpre"))),1)
    def test_lexical_aliases_fail_before_receipts_or_carriers(self):
        (self.root/"nested").mkdir()
        source=self.source("nested/a.md",b"fixture")
        for alias in ("./nested/a.md","nested//a.md","nested/./a.md","nested/a.md/","nested/a.md/.","nested/a.md\x00","nested/a.md\n"):
            with self.subTest(alias=alias),self.assertRaisesRegex(ValueError,"PATH_HOLD"):
                intake.ingest(self.root,self.load,alias)
        self.assertEqual(self.receipts(),[])
        self.assertEqual(list((self.load/"R0_PACKS_private").iterdir()),[])
        self.assertEqual(source.read_bytes(),b"fixture")
        a=intake.ingest(self.root,self.load,"nested/a.md")
        b=intake.ingest(self.root,self.load,"nested/a.md")
        self.assertEqual(a["occurrence"],b["occurrence"])
        self.assertEqual(a["receipt_sha256"],b["receipt_sha256"])
        self.assertEqual(len(self.receipts()),1)
    def test_tamper_denied(self):
        p=self.source("x.md",b"# Fixture")
        a=intake.ingest(self.root,self.load,p.name)
        carrier=self.load/"R0_PACKS_private"/(a["sha256"]+".cgxpre")
        blob=carrier.read_bytes()
        for broken in (b"bad"+blob[3:],blob+b"trailing",blob[:49],blob[:17]+bytes(32)+blob[49:]):
            with self.assertRaises((ValueError,zlib.error)):
                intake.restore(broken,a["sha256"])
        carrier.write_bytes(blob+b"trailing")
        with self.assertRaises((ValueError,zlib.error)):
            intake.ingest(self.root,self.load,p.name)
        self.assertEqual(p.read_bytes(),b"# Fixture")
    def test_path_and_size_denied(self):
        for bad in ("../outside.md","/absolute.md","C:/absolute.md","a\\b.md",""):
            with self.assertRaises((ValueError,OSError)):
                intake.read_source(self.root,bad)
        for name,raw in (("empty",b""),("large",b"x"*(intake.MAX_FILE+1))):
            self.source(name,raw)
            with self.assertRaises(ValueError):
                intake.read_source(self.root,name)
    def test_store_and_authority_hold(self):
        p=self.source("a.json",b'{"value":1}')
        guard=self.load/"INTEGRITY_AND_GC_GATES.review.json"
        guard.write_text("{}",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"LOAD_CONTRACT_HOLD"):
            intake.ingest(self.root,self.load,p.name)
        guard.write_text('{"schema":"CGX-LOAD-INTAKE-AUDIT/0.17"}',encoding="utf-8")
        a=intake.ingest(self.root,self.load,p.name)
        record=json.loads((self.load/"Local_batch_receipts"/a["receipt"]).read_bytes())
        for k in ("acl_verified","native_admitted","data_space_admitted","source_deleted"):
            self.assertIs(record[k],False)
        self.assertEqual(record["rights"],"UNREVIEWED_PRIVATE")
    def test_static_code_not_executed(self):
        p=self.source("fixture.py",b'raise RuntimeError("must not execute")\ndef f():\n    return 1\n')
        a=intake.ingest(self.root,self.load,p.name)
        r=json.loads((self.load/"Local_batch_receipts"/a["receipt"]).read_bytes())
        self.assertEqual(r["data_projection"]["functions"],["f"])
        self.assertEqual(r["view_kind"],"STATIC_CODE_STRUCTURE")
        self.assertIs(r["semantic_projection"]["scientific_validation"],False)
    def test_binary_and_bad_json_hold(self):
        for name,raw in (("a.bin",b"\xff\x00"),("b.json",b"{invalid")):
            self.source(name,raw)
            a=intake.ingest(self.root,self.load,name)
            self.assertEqual(a["view_kind"],"BYTE_ONLY")
            self.assertEqual(a["semantic_state"],"VIEW_HOLD")
            self.assertTrue(a["exact_inverse"])
    def test_collision_no_overwrite(self):
        p=self.root/"collision"
        self.assertTrue(intake.put_exact(p,b"first"))
        self.assertFalse(intake.put_exact(p,b"first"))
        with self.assertRaises(ValueError):
            intake.put_exact(p,b"second")
        self.assertEqual(p.read_bytes(),b"first")
if __name__=="__main__":
    unittest.main(verbosity=2)
