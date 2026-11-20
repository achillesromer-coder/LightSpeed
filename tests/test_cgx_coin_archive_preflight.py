"""Synthetic-only refusal tests for the non-extracting COIN archive preflight."""
import copy
import hashlib
import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from cgx_coin_archive_preflight import audit, ArchiveHold

PREFIX="CoinArchiveTest/"
RECEIPT={"production_authorised":False,"inventory":{"manifested_files":2,"json_schemas":1,"default_solidity_sources":1,"gated_disabled_templates":1}}
CANON={
 "record_id":"coin-protocol-canon-2026-07-29",
 "drive":{},
 "implementation":{"full_source_published_to_public_git":False,"solidity_compiled":False,"independent_security_audit_complete":False},
 "feature_gates":{"public_token":False,"public_sale":False},
}
def encode(value): return json.dumps(value,sort_keys=True).encode("utf8")
def sha(raw): return hashlib.sha256(raw).hexdigest()
class ArchiveTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/"test.zip"
  self.manifest=None
  self.coin=None
  self.write()
 def write(self, *, corrupt_payload=False, extra=False, traversal=False, duplicate=False, symlink=False, production=False):
  payload=b"synthetic test bytes only"
  receipt=copy.deepcopy(RECEIPT)
  receipt["production_authorised"]=production
  rb=encode(receipt)
  rows=[
   {"path":"payload.txt","sha256":sha(payload),"size_bytes":len(payload)},
   {"path":"BUILD_RECEIPT.json","sha256":sha(rb),"size_bytes":len(rb)},
  ]
  manifest={"production_authorised":False,"files":rows}
  self.manifest=manifest
  with zipfile.ZipFile(self.path,"w",compression=zipfile.ZIP_DEFLATED) as z:
   z.writestr(PREFIX+"payload.txt",b"changed" if corrupt_payload else payload)
   z.writestr(PREFIX+"BUILD_RECEIPT.json",rb)
   z.writestr(PREFIX+"protocol-manifest.json",encode(manifest))
   if extra: z.writestr(PREFIX+"unexpected.txt",b"not in manifest")
   if traversal:z.writestr(PREFIX+"../unsafe.txt",b"unsafe")
   if duplicate:
    with warnings.catch_warnings():
     warnings.simplefilter("ignore",UserWarning)
     z.writestr(PREFIX+"payload.txt",payload)
   if symlink:
    info=zipfile.ZipInfo(PREFIX+"sym")
    info.create_system=3
    info.external_attr=(0o120777 << 16)
    z.writestr(info,b"linktarget")
  self.coin=copy.deepcopy(CANON)
  self.coin["drive"]={"archive_sha256":sha(self.path.read_bytes()),"archive_size_bytes":self.path.stat().st_size}
 def assertHeld(self, coin=None):
  with self.assertRaises(ArchiveHold):audit(self.path,coin or self.coin)
 def test_valid_archive(self):
  out=audit(self.path,self.coin)
  self.assertEqual(out["status"],"ARCHIVE_VERIFIED_NOT_DEPLOYED")
  self.assertEqual(out["manifested_files_verified"],2)
  self.assertFalse(out["contract_compilation_proven"])
 def test_hash_drift(self):
  bad=copy.deepcopy(self.coin);bad["drive"]["archive_sha256"]="0"*64
  self.assertHeld(bad)
 def test_size_drift(self):
  bad=copy.deepcopy(self.coin);bad["drive"]["archive_size_bytes"]+=1
  self.assertHeld(bad)
 def test_manifest_payload_mismatch(self):
  self.write(corrupt_payload=True)
  self.assertHeld()
 def test_unmanifested_file(self):
  self.write(extra=True)
  self.assertHeld()
 def test_traversal(self):
  self.write(traversal=True)
  self.assertHeld()
 def test_duplicate_path(self):
  self.write(duplicate=True)
  self.assertHeld()
 def test_symlink(self):
  self.write(symlink=True)
  self.assertHeld()
 def test_production_declared_in_archive(self):
  self.write(production=True)
  self.assertHeld()
 def test_public_gate_denied(self):
  bad=copy.deepcopy(self.coin);bad["feature_gates"]["public_token"]=True
  self.assertHeld(bad)
 def test_fake_solidity_compilation_denied(self):
  bad=copy.deepcopy(self.coin);bad["implementation"]["solidity_compiled"]=True
  self.assertHeld(bad)
 def test_missing_canonical_identity_denied(self):
  bad=copy.deepcopy(self.coin);bad["record_id"]="other root"
  self.assertHeld(bad)
 def test_explicit_false_not_integer(self):
  bad=copy.deepcopy(self.coin);bad["feature_gates"]["public_sale"]=0
  self.assertHeld(bad)

if __name__ == "__main__":
 unittest.main()
