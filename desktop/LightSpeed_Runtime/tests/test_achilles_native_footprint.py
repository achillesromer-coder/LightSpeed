import json,hashlib,tempfile,unittest
from pathlib import Path
from lightspeed_runtime.achilles.native_footprint import inventory

class FootprintTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/"manifests").mkdir();(self.root/"blobs").mkdir()
    def blob(self,data,kind="application/vnd.ollama.image.model"):
        h=hashlib.sha256(data).hexdigest();(self.root/"blobs"/("sha256-"+h)).write_bytes(data)
        return {"digest":"sha256:"+h,"size":len(data),"mediaType":kind}
    def write(self,name,config,layers):
        (self.root/"manifests"/name).write_text(json.dumps({"schemaVersion":2,"config":config,"layers":layers}),encoding="utf8")
    def test_shared(self):
        c=self.blob(b"cfg","config");a=self.blob(b"weights")
        self.write("A",c,[a]);self.write("B",c,[a])
        b=inventory(self.root)["review"]
        self.assertEqual((b["size_matched_reference_bytes"],b["size_matched_unique_blob_bytes"],b["repeated_reference_bytes"]),(20,10,10))
        self.assertEqual(b["unique_weight_blob_bytes"],7)
        self.assertFalse(b["blob_content_hash_verified"])
    def test_missing_mismatch_cloud(self):
        c=self.blob(b"cfg","config");a=self.blob(b"weights")
        (self.root/"blobs"/a["digest"].replace(":","-")).write_bytes(b"x")
        self.write("A",c,[a]);self.write("cloud",c,None)
        b=inventory(self.root)["review"]
        self.assertEqual(b["size_mismatch_count"],1)
        self.assertEqual(b["unique_weight_blob_bytes"],0)
        self.assertTrue(b["manifests"][1]["cloud_or_no_weight_layers"])
        (self.root/"blobs"/a["digest"].replace(":","-")).unlink()
        self.assertEqual(inventory(self.root)["review"]["missing_blob_count"],1)
    def test_conflict(self):
        c=self.blob(b"cfg","config");a=self.blob(b"x")
        self.write("A",c,[a]);self.write("B",c,[dict(a,size=9)])
        with self.assertRaises(ValueError):inventory(self.root)
    def test_path_and_schema(self):
        c=self.blob(b"cfg","config")
        self.write("A",c,[dict(c,digest="../../bad")])
        with self.assertRaises(ValueError):inventory(self.root)
        self.write("A",c,[dict(c,size=True)])
        with self.assertRaises(ValueError):inventory(self.root)
