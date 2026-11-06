import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from package_unispace_premint import create,canonical,digest,extract_shell

class ShellPackagingTests(unittest.TestCase):
 def setUp(self):
    self.temp=tempfile.TemporaryDirectory()
    self.root=Path(self.temp.name)
    self.build=self.root/"dist"
    self.viewer=self.root/"viewer"
    (self.build/"assets").mkdir(parents=True)
    self.build.joinpath("index.html").write_text(
      '<script src="/assets/main.js"></script><link rel="stylesheet" href="/assets/main.css">',
      encoding="utf-8")
    self.build.joinpath("assets/main.js").write_text(
      'console.log("CGX first-spaces lattice");console.log("Export concept review JSON");',
      encoding="utf-8")
    self.build.joinpath("assets/main.css").write_text("body{display:block}",encoding="utf-8")
    names=["cgx/index.html","cgx/doom/index.html","cgx/fs/index.html",
           "cgx/ds/index.html","cgx/ps/index.html","cgx/eco/index.html",
           "cgx/romer/index.html","cgx/assets/core.js","cgx/assets/viewer.js",
           "cgx/assets/viewer.css","cgx/assets/domain-overviews.js",
           "cgx/assets/domain-viewer.js"]
    assets=[]
    for name in names:
        dst=self.viewer/name
        dst.parent.mkdir(parents=True,exist_ok=True)
        body=f"fake-public-fixture:{name}".encode()
        dst.write_bytes(body)
        assets.append({"path":name,"sha256":digest(body),"bytes":len(body)})
    self.viewer.joinpath("cgx-package-review.json").write_bytes(canonical({
       "schema":"CGX-PUBLIC-ALLOWLIST-PACKAGE/0.1",
       "status":"SOURCE_CANDIDATE_NOT_PUBLISHED_NOT_OWNER_SIGNED",
       "file_count":12,"source_bytes":sum(x["bytes"] for x in assets),
       "assets":assets
    }))
 def tearDown(self):self.temp.cleanup()
 def test_public_shell_and_viewer_zip_are_deterministic_and_data_excluded(self):
    (self.build/"data").mkdir()
    (self.build/"data/private.json").write_text('SECRETS_MUST_NOT_SHIP')
    (self.build/"physical-operations-seed.json").write_text('NOT_FOR_RELEASE')
    first=create(self.build,self.viewer,self.root/"first.zip")
    second=create(self.build,self.viewer,self.root/"second.zip")
    self.assertEqual(first["archive_sha256"],second["archive_sha256"])
    with zipfile.ZipFile(self.root/"first.zip") as z:
       names=set(z.namelist())
       self.assertIn("MANIFEST.json",names)
       self.assertIn("shell/index.html",names)
       self.assertIn("viewer/cgx/index.html",names)
       self.assertNotIn("shell/data/private.json",names)
       self.assertNotIn("shell/physical-operations-seed.json",names)
       manifest=json.loads(z.read("MANIFEST.json"))
       self.assertFalse(manifest["public_release_approved"])
       self.assertFalse(manifest["rights_qualified"])
       self.assertEqual(len(json.loads(z.read("metadata/first-spaces-lattice.json"))["nodes"]),11)
       self.assertNotIn("SECRETS_MUST_NOT_SHIP",b"".join(z.read(x) for x in names).decode())
 def test_refuse_external_or_unlisted_script(self):
    (self.build/"index.html").write_text('<script src="https://outside/evil.js"></script>'+
       '<link rel="stylesheet" href="/assets/main.css">')
    with self.assertRaisesRegex(ValueError,"EXTERNAL_OR_UNSAFE_ASSET_REFERENCE"):
       create(self.build,self.viewer,self.root/"bad.zip")
 def test_refuse_viewer_source_tampering(self):
    (self.viewer/"cgx/index.html").write_bytes(b"tampered")
    with self.assertRaisesRegex(ValueError,"PUBLIC_VIEWER_SOURCE_DIGEST_DRIFT"):
       create(self.build,self.viewer,self.root/"bad.zip")
 def test_refuse_secret_in_compiled_shell(self):
    (self.build/"assets/main.js").write_bytes(
      b'CGX first-spaces lattice Export concept review JSON sk-proj-private')
    with self.assertRaisesRegex(ValueError,"KEY_OR_SECRET_SIGNATURE"):
       create(self.build,self.viewer,self.root/"bad.zip")
 def test_existing_output_is_never_overwritten(self):
    existing=self.root/"exists.zip";existing.write_bytes(b"owner")
    with self.assertRaisesRegex(ValueError,"PACKAGE_ALREADY_EXISTS"):
       create(self.build,self.viewer,existing)
    self.assertEqual(existing.read_bytes(),b"owner")
if __name__=="__main__": unittest.main()
