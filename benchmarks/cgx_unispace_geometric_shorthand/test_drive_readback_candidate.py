import hashlib
import tempfile
import unittest
from pathlib import Path
from drive_readback_candidate import resolve_key

def packet(data=b"example"):
    return {
        "action":"source_root_readback_only",
        "authority_transfer":False,
        "handoff":"CGX-UNISPACE-R0-DRIVE-READBACK-20261012",
        "mode":"review_only",
        "schema":"cgx.drive.minimal-reference-candidate.v1",
        "source":{"bytes":len(data),"ref":"drive:file:fixture",
                  "sha256":hashlib.sha256(data).hexdigest()},
        "target":"BouwerBase",
    }

class DriveKeyCandidateTests(unittest.TestCase):
    def test_missing_is_not_cached(self):
        r,fresh=resolve_key(packet(),asset=None)
        self.assertEqual(r["status"],"NOT_CACHED")
        self.assertTrue(fresh)
    def test_exact_root_and_duplicate_no_action(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"source"
            path.write_bytes(b"example")
            r,change=resolve_key(packet(),asset=path)
            self.assertTrue(change)
            self.assertEqual(r["status"],"RESOLVED_LOCAL_REFERENCE")
            self.assertFalse(r["lease_verified"])
            self.assertFalse(r["execution_performed"])
            self.assertFalse(resolve_key(packet(),asset=path,previous=r)[1])
            path.write_bytes(b"examplE")
            rr,change=resolve_key(packet(),asset=path,previous=r)
            self.assertEqual(rr["status"],"CONTEXT_MISMATCH")
            self.assertTrue(change)
    def test_uncached_state_does_not_suppress_later_resolution(self):
        old,_=resolve_key(packet())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"source"
            path.write_bytes(b"example")
            result,fresh=resolve_key(packet(),asset=path,previous=old)
            self.assertTrue(fresh)
            self.assertEqual(result["status"],"RESOLVED_LOCAL_REFERENCE")
    def test_unauthorised_operation_rejected(self):
        key=packet()
        key["action"]="command"
        with self.assertRaises(ValueError):
            resolve_key(key)
    def test_invalid_rights_and_target_rejected(self):
        for field,value in (("mode","execute"),("target","ANYNODE"),("authority_transfer",True)):
            key=packet()
            key[field]=value
            with self.assertRaises(ValueError):
                resolve_key(key)
    def test_no_literal_path_from_key(self):
        key=packet()
        key["source"]["ref"]="C:/Users/owner/secrets"
        with self.assertRaises(ValueError):
            resolve_key(key)
