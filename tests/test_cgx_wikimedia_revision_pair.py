"""Synthetic, source-byte-aware Wikimedia API fixtures; NOT real wiki snapshots."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/"cgx"/"portable_node"/"wikimedia_revision_pair.py"
spec=importlib.util.spec_from_file_location("cgx_wikimedia_revision_pair",PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ITEM="Q987654321"

def raw(value):
    return json.dumps(value,ensure_ascii=False,separators=(",",":")).encode("utf-8")

def response(site, title, pageid, revid, text):
    return {"batchcomplete":True,"query":{"pages":[{
        "pageid":pageid,"ns":0,"title":title,
        "pageprops":{"wikibase_item":ITEM},
        "revisions":[{"revid":revid,"timestamp":"2026-10-19T12:00:00Z",
                      "slots":{"main":{"contentmodel":"wikitext","content":text}}}]
    }]}}

EN=response("enwiki","Synthetic test article",123,456,
            "A synthetic [[Category:Example|Example]] and [[Node]] {{Template}}")
FR=response("frwiki","Article de test synthétique",789,1011,
            "Une entrée [[Catégorie:Exemple]] et [[Nœud]] {{Modèle}}")
WD={"entities":{ITEM:{"id":ITEM,"lastrevid":54321,"sitelinks":{
     "enwiki":{"site":"enwiki","title":"Synthetic test article"},
     "frwiki":{"site":"frwiki","title":"Article de test synthétique"}}}}}

def compile_pair(en=EN,fr=FR,wd=WD):
    return m.compile_wikimedia_pair(raw(en),raw(fr),raw(wd),requested_item=ITEM)

class WikimediaRevisionPairTests(unittest.TestCase):
    def test_distinct_language_pages_same_item_without_translation_claim(self):
        p=compile_pair()
        self.assertEqual(p["schema"],"CGX-ALEXANDRIA-WIKIMEDIA-API-PAIR/0.1")
        self.assertEqual(len(p["pages"]),2)
        self.assertEqual([x["language"] for x in p["pages"]],["en","fr"])
        self.assertEqual([x["pageid"] for x in p["pages"]],[123,789])
        self.assertEqual([x["revision_id"] for x in p["pages"]],[456,1011])
        self.assertNotEqual(p["pages"][0]["candidate_ref"],p["pages"][1]["candidate_ref"])
        self.assertEqual(p["pages"][0]["shared_wikidata_item"],ITEM)
        self.assertEqual(p["pages"][1]["shared_wikidata_item"],ITEM)
        self.assertEqual(p["edges"][0]["relation"],"WIKIDATA_SITELINK_ASSOCIATION_NOT_TRANSLATION")
        self.assertFalse(p["translation_equivalence_proven"])
        self.assertFalse(p["native_dbr_verified"])
        self.assertFalse(p["wiki_corpus_complete"])
        self.assertFalse(p["provider_transport_authenticated"])
        self.assertFalse(p["canon_admitted"])
        self.assertFalse(p["source_bytes_embedded"])

    def test_original_sha_and_revision_citations(self):
        import hashlib
        p=compile_pair()
        for page, original in zip(p["pages"],(EN,FR)):
            content=original["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
            self.assertEqual(page["wikitext_sha256"],hashlib.sha256(content.encode("utf-8")).hexdigest())
            self.assertEqual(page["wikitext_utf8_bytes"],len(content.encode("utf-8")))
            self.assertEqual(page["licence"],"CC-BY-SA-4.0")
            self.assertTrue(page["revision_permalink"].endswith("oldid="+str(page["revision_id"])))
            self.assertTrue(page["source_history_url"].endswith("action=history"))
            self.assertFalse(page["links_complete"])
            self.assertFalse(page["redirects_complete"])
            self.assertFalse(page["templates_expanded"])
            self.assertFalse(page["media_acquired"])
        self.assertEqual(p["wikidata"]["licence"],"CC0-1.0")
        self.assertEqual(p["wikidata"]["lastrevid"],54321)

    def test_language_sitelink_mismatch_fails_closed(self):
        bad=copy.deepcopy(WD)
        bad["entities"][ITEM]["sitelinks"]["frwiki"]["title"]="False identity"
        with self.assertRaisesRegex(ValueError,"sitelink"):
            compile_pair(wd=bad)
        bad2=copy.deepcopy(FR)
        bad2["query"]["pages"][0]["pageprops"]["wikibase_item"]="Q2"
        with self.assertRaisesRegex(ValueError,"Wikidata identity"):
            compile_pair(fr=bad2)

    def test_invalid_revision_and_missing_source_body_rejected(self):
        for alteration in ("deleted","wrong_revision","wrong_ns","multiple","missing_time"):
            bad=copy.deepcopy(EN)
            p=bad["query"]["pages"][0]
            rev=p["revisions"][0]
            if alteration=="deleted":
                del rev["slots"]["main"]["content"]
            elif alteration=="wrong_revision":
                rev["revid"]=0
            elif alteration=="wrong_ns":
                p["ns"]=14
            elif alteration=="multiple":
                p["revisions"].append(copy.deepcopy(rev))
            else:
                rev["timestamp"]="no date"
            with self.subTest(alteration=alteration),self.assertRaises(ValueError):
                compile_pair(en=bad)

    def test_untrusted_api_json_rejected(self):
        a=raw(EN)
        good_fr=raw(FR)
        good_wd=raw(WD)
        for invalid in (b"",b"{}",b'{"query":1,"query":2}',b'{"query":NaN}',
                        b"\xff",b"[]" ,b"a"*(m.MAX_RESPONSE_BYTES+1)):
            with self.subTest(invalid=invalid[:30]),self.assertRaises((ValueError,UnicodeError,TypeError)):
                m.compile_wikimedia_pair(invalid,good_fr,good_wd,requested_item=ITEM)
        with self.assertRaises(ValueError):
            m.compile_wikimedia_pair(a,good_fr,good_wd,requested_item="INVALID")

    def test_no_cross_namespace_or_missing_sitelinks(self):
        wd=copy.deepcopy(WD)
        del wd["entities"][ITEM]["sitelinks"]["frwiki"]
        with self.assertRaisesRegex(ValueError,"sitelink"):
            compile_pair(wd=wd)
        fr=copy.deepcopy(FR)
        fr["query"]["pages"][0]["pageid"]=-1
        with self.assertRaises(ValueError):
            compile_pair(fr=fr)

    def test_only_bounded_lexical_candidates_no_claim_of_link_completeness(self):
        result=compile_pair()
        self.assertEqual(result["pages"][0]["lexical_wikilink_targets"],["Category:Example","Node"])
        self.assertFalse(result["pages"][0]["links_complete"])
        self.assertIn("TEMPLATE_REDIRECT_AND_OUTLINK_COMPLETENESS",result["frontier"])
        self.assertTrue(result["source_bytes_embedded"] is False)

    def test_provider_response_required_and_not_equated_to_verified_transport(self):
        result=compile_pair()
        self.assertEqual(result["status"],"API_BYTES_STRUCTURALLY_VERIFIED_PROVIDER_ORIGIN_UNATTESTED")
        self.assertFalse(result["original_api_responses_persisted_by_compiler"])
        self.assertIn("CONFIRM_OFFICIAL_PROVIDER_BYTES_AND_REVISION_PERMALINKS",result["frontier"])

if __name__=="__main__":
    unittest.main()
