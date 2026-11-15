import io,json,os,unittest,zipfile,hashlib,tempfile
from pathlib import Path
from package_unispace_premint import canonical,digest
from package_unispace_uos_integration import (
 PROJECT,PRIVATE_ALLOWLIST,SCHEMA,index_bytes,list_runtime_paths,
 runtime_assets,verify_uos_archive,create,uos_artifacts)
from test_package_unispace_premint import ShellPackagingTests
class UosPackagingTests(ShellPackagingTests):
 def test_native_runtime_git_index_is_bound_and_source_only(self):
    assets,count=runtime_assets(PROJECT)
    self.assertGreaterEqual(count,80)
    self.assertTrue(all(k.startswith("native/") for k in assets))
    self.assertTrue(any(k.endswith("/runtime.py") for k in assets))
    self.assertFalse(any("private" in k.lower() or "data/" in k.lower() for k in assets))
    self.assertTrue(any(k.endswith("requirements-core.txt") for k in assets))
 def test_full_private_uos_candidate_receipts_and_fail_closed_gates(self):
    z=self.root/"uos.zip"
    r=create(self.build,self.viewer,z)
    self.assertEqual(r["state"],"PRIVATE_INTEGRATION_PACKAGED_NOT_PUBLIC")
    self.assertGreaterEqual(r["native_modules"],80)
    with zipfile.ZipFile(z) as f:
       m=verify_uos_archive(z)
       self.assertFalse(m["public_release_allowed"])
       self.assertFalse(m["signed"])
       self.assertFalse(m["native_minted"])
       self.assertFalse(m["ccc_network_activated"])
       self.assertEqual(m["release_blockers"],list(PRIVATE_ALLOWLIST))
       self.assertIn("native/lightspeed_runtime/runtime.py",f.namelist())
       self.assertIn("shell/index.html",f.namelist())
       self.assertIn("viewer/cgx/index.html",f.namelist())
       self.assertNotIn("shell/data/cgx_internal_review_projection.json",f.namelist())
       self.assertNotIn("native/secrets.json",f.namelist())
       self.assertNotIn("UOS_FULLY_OPERATIONAL_SIGNED_INSTALLER.exe",f.namelist())
    self.assertEqual(r["sha256"],digest(z.read_bytes()))
 def test_unauthorised_release_claims_in_manifest_are_rejected(self):
    out=self.root/"fake.zip"
    with zipfile.ZipFile(out,"w") as z:
      z.writestr("UOS_INTEGRATION_MANIFEST.json",canonical({
        "schema":SCHEMA,"public_release_allowed":True,
        "native_minted":False,"contents":[]}))
    with self.assertRaisesRegex(ValueError,"UNSAFE_RELEASE_MANIFEST"):
      verify_uos_archive(out)
 def test_manifest_tampering_and_conflicting_source_paths_are_rejected(self):
    files,m=uos_artifacts(self.build,self.viewer,PROJECT)
    self.assertTrue(len(files)>80)
    with zipfile.ZipFile(self.root/"bad.zip","w") as z:
      for k,data in files.items():
        z.writestr(k,b"tampered" if k=="native/lightspeed_runtime/contracts.py" else data)
    with self.assertRaisesRegex(ValueError,"ARCHIVE_DIGEST_MISMATCH"):
      verify_uos_archive(self.root/"bad.zip")
 def test_package_does_not_overwrite_owner_archive(self):
    dest=self.root/"existing.zip";dest.write_bytes(b"owner-preserved")
    with self.assertRaisesRegex(ValueError,"PACKAGE_ALREADY_EXISTS"):
      create(self.build,self.viewer,dest)
    self.assertEqual(dest.read_bytes(),b"owner-preserved")

class UosAdversarialManifestTests(ShellPackagingTests):
 def test_self_consistent_archive_cannot_elevate_authority_or_hide_members(self):
    import copy
    original,manifest=uos_artifacts(self.build,self.viewer,PROJECT)
    def write_case(files,m,name):
       files=dict(files);files["UOS_INTEGRATION_MANIFEST.json"]=canonical(m)
       target=self.root/(name+".zip")
       with zipfile.ZipFile(target,"w") as z:
          for k,v in files.items():z.writestr(k,v)
       return target
    for field in ("signed","ccc_network_activated","physical_devices_paired",
                  "source_deleted","all_gates_accepted"):
       with self.subTest(field=field):
          m=copy.deepcopy(manifest);m[field]=True
          with self.assertRaisesRegex(ValueError,"UNSAFE_RELEASE_MANIFEST"):
             verify_uos_archive(write_case(original,m,field))
    with self.subTest(case="duplicate_manifest_entry_hides_extra"):
       m=copy.deepcopy(manifest);files=dict(original)
       files["extra.txt"]=b"unexpected";m["contents"].append(m["contents"][0])
       with self.assertRaisesRegex(ValueError,"ARCHIVE_MEMBERSHIP_MISMATCH"):
          verify_uos_archive(write_case(files,m,"duplicate"))
    with self.subTest(case="path_traversal"):
       m=copy.deepcopy(manifest);files=dict(original);files["../escape.txt"]=b"escape"
       m["contents"].append({"path":"../escape.txt","sha256":digest(b"escape"),"bytes":6})
       with self.assertRaisesRegex(ValueError,"UNSAFE_ARCHIVE_PATH"):
          verify_uos_archive(write_case(files,m,"traversal"))
    with self.subTest(case="rehashed_runtime_auto_execute"):
       m=copy.deepcopy(manifest);files=dict(original)
       key="metadata/native-runtime-policy.json";v=json.loads(files[key]);v["runtime_execute_automatically"]=True
       files[key]=canonical(v)
       for a in m["contents"]:
          if a["path"]==key:a.update(sha256=digest(files[key]),bytes=len(files[key]))
       with self.assertRaisesRegex(ValueError,"UNSAFE_RUNTIME_POLICY"):
          verify_uos_archive(write_case(files,m,"policy"))
