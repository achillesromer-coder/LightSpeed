"""Deterministic mocked-transport acquisition tests; no live Wikimedia fetch."""
import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "wikimedia_acquisition", ROOT/"scripts"/"acquire_wikimedia_revision_pair.py")
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
Q="Q987654321"
CUTOFF="2026-10-20T12:00:00Z"

def encode(x):
    return json.dumps(x,ensure_ascii=False).encode("utf-8")

def mock_responses():
    def wiki(title,page_id,revision,text):
        return {"query":{"pages":[{
            "pageid":page_id,"ns":0,"title":title,
            "pageprops":{"wikibase_item":Q},
            "revisions":[{
                "revid":revision,
                "timestamp":"2026-10-19T12:00:00Z",
                "slots":{"main":{"contentmodel":"wikitext","content":text}}
            }]
        }]}}
    wd={"entities":{Q:{"id":Q,"lastrevid":4567,"sitelinks":{
        "enwiki":{"site":"enwiki","title":"Synthetic English page"},
        "frwiki":{"site":"frwiki","title":"Page française synthétique"}}}}}
    return {
        "www.wikidata.org":encode(wd),
        "en.wikipedia.org":encode(wiki("Synthetic English page",101,201,"A [[Source]]")),
        "fr.wikipedia.org":encode(wiki("Page française synthétique",102,202,"B [[Source]]"))
    }

def fake_fetch(records,seen):
    def get(url):
        parts=urlsplit(url)
        seen.append(parts)
        assert parts.scheme=="https"
        assert parts.hostname in records
        query=parse_qs(parts.query)
        if parts.hostname!="www.wikidata.org":
            assert query["rvstart"]==[CUTOFF]
            assert query["rvslots"]==["main"]
            assert query["rvlimit"]==["1"]
        return records[parts.hostname]
    return get

class WikimediaAcquisitionTests(unittest.TestCase):
    def test_all_original_api_bytes_saved_only_in_explicit_private_folder(self):
        rows=mock_responses()
        calls=[]
        with tempfile.TemporaryDirectory() as temp:
            output=pathlib.Path(temp)/"owner-private-r0"
            manifest=mod.acquire_wikimedia_pair(Q,CUTOFF,output,
                      fetcher=fake_fetch(rows,calls))
            self.assertEqual(len(calls),3)
            self.assertEqual(len(manifest["records"]),3)
            self.assertFalse(manifest["native_dbr_verified"])
            self.assertFalse(manifest["provider_origin_independently_attested"])
            self.assertFalse(manifest["licensing_review_required"] is False)
            for record in manifest["records"]:
                original=rows[urlsplit(record["source_url"]).hostname]
                self.assertEqual((output/record["file"]).read_bytes(),original)
                self.assertEqual(record["bytes"],len(original))
            derived=json.loads((output/"r1_candidate.json").read_text())
            self.assertEqual([x["pageid"] for x in derived["pages"]],[101,102])
            self.assertEqual(derived["requested_item"],Q)
            self.assertFalse(derived["translation_equivalence_proven"])
            self.assertFalse(derived["canon_admitted"])
            self.assertFalse(derived["source_bytes_embedded"])
            self.assertEqual(derived["pages"][0]["revision_id"],201)

    def test_bad_request_or_existing_target_never_calls_provider(self):
        def forbid(_url):
            raise AssertionError("network access should not start")
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/"private"
            for item,cutoff,path in [
                ("INVALID",CUTOFF,out),(Q,"tomorrow",out),
                (Q,CUTOFF,pathlib.Path(temp)/"public"/"test"),
                (Q,CUTOFF,pathlib.Path(temp)/"dist"/"test")]:
                with self.subTest(item=item,cutoff=cutoff,path=str(path)),self.assertRaises(ValueError):
                    mod.acquire_wikimedia_pair(item,cutoff,path,fetcher=forbid)
            out.mkdir()
            (out/"original").write_text("PRESERVE")
            with self.assertRaisesRegex(ValueError,"already exist"):
                mod.acquire_wikimedia_pair(Q,CUTOFF,out,fetcher=forbid)
            self.assertEqual((out/"original").read_text(),"PRESERVE")

    def test_bad_sitelink_or_tampered_source_never_mutates_target(self):
        records=mock_responses()
        modified=copy.deepcopy(json.loads(records["www.wikidata.org"]))
        modified["entities"][Q]["sitelinks"]["frwiki"]["title"]="Mismatch"
        records["www.wikidata.org"]=encode(modified)
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/"private"
            with self.assertRaisesRegex(ValueError,"sitelink"):
                mod.acquire_wikimedia_pair(Q,CUTOFF,out,fetcher=fake_fetch(records,[]))
            self.assertFalse(out.exists())

    def test_revision_newer_than_cutoff_rejected(self):
        records=mock_responses()
        modified=json.loads(records["en.wikipedia.org"])
        modified["query"]["pages"][0]["revisions"][0]["timestamp"]="2026-10-21T00:00:00Z"
        records["en.wikipedia.org"]=encode(modified)
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/"private"
            with self.assertRaisesRegex(ValueError,"exceeds requested cutoff"):
                mod.acquire_wikimedia_pair(Q,CUTOFF,out,fetcher=fake_fetch(records,[]))
            self.assertFalse(out.exists())

    def test_disallows_arbitrary_source_origins(self):
        with self.assertRaisesRegex(ValueError,"unapproved"):
            mod.request_url("https://attacker.invalid/api",{"action":"query"})
        url=mod.request_url(mod.ORIGINS[1],{"action":"query","titles":"A B"})
        self.assertIn("titles=A+B",url)
        self.assertEqual(urlsplit(url).hostname,"en.wikipedia.org")

if __name__=="__main__":
    unittest.main()
