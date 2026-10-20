"""Offline Alexandria source-only training index: accessibility and rights gates."""
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"cgx/review/alexandria_offline_reference_preview.py"
spec=importlib.util.spec_from_file_location("alexandria_preview",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CountRows(HTMLParser):
    def __init__(self):
        super().__init__();self.entries=0
    def handle_starttag(self,tag,attrs):
        if tag=="tr" and dict(attrs).get("data-entry"):
            self.entries+=1

class OfflineReferenceTests(unittest.TestCase):
    def test_all_238_source_entries_are_source_only(self):
        h=m.build_offline_reference_html()
        parser=CountRows();parser.feed(h)
        self.assertEqual(parser.entries,238)
        self.assertIn("Learning pathways",h)
        self.assertIn("Content-Security-Policy",h)
        self.assertIn("connect-src &#x27;none&#x27;",h)
        self.assertNotIn("<script src=",h.lower())
        self.assertNotIn("fetch(",h)
        self.assertNotIn("XMLHttpRequest",h)
        self.assertNotIn("private_key",h)
        self.assertNotIn("access_token",h)
    def test_input_text_and_external_urls_escape_safely(self):
        self.assertEqual(m._e('<img src=x onerror="alert(1)">'),
                         '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;')
        for url in ["javascript:alert(1)","file:///etc/passwd","http://github.com/a/b",
                    "https://localhost/secret","https://127.0.0.1/data",
                    "https://user:pass@example.com/secret",
                    "https://example.com/path?token=private"]:
            self.assertIsNone(m.safe_external_reference(url))
        self.assertEqual(m.safe_external_reference("https://github.com/godotengine/godot"),
                         "https://github.com/godotengine/godot")
    def test_generating_preview_requires_no_user_secrets_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            filename=str(Path(tmp)/"alexandria-offline.html")
            p=subprocess.run([sys.executable,str(P),"--output",filename],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            data=Path(filename).read_text()
            self.assertEqual(data,m.build_offline_reference_html())
            self.assertNotIn('src="https:',data)
            self.assertNotIn("HOLD_PUBLIC_RELEASE</",data)
            self.assertIn("Review-only",data)
    def test_no_automatic_public_release_claim(self):
        h=m.build_offline_reference_html()
        self.assertIn("not an authorised public release of UniSpace",h)
        self.assertIn("source link is not redistribution permission",h.lower())
        self.assertIn("game data",h)
if __name__=="__main__":
    unittest.main()
