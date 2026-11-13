"""Review-only keyed FileSpace/DataSpace and external intake acceptance tests."""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODE = ROOT / "cgx" / "portable_node" / "keyed_fileset_plan.py"
SPEC = importlib.util.spec_from_file_location("cgx_keyed_fileset_plan", CODE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
REVIEW = ROOT / "cgx" / "review"

def example(mode="REFERENCES_ONLY", audience="PUBLIC", redistribution="UNVERIFIED"):
    return {
        "schema": "CGX-FILESET-SOURCE-PROPOSAL/0.1",
        "fileset_id": "cgx:alexandria:demo",
        "mode": mode, "audience": audience,
        "components": [{
            "source_id": "external:example:game",
            "sha256": "a"*64, "byte_length": 345,
            "redistribution": redistribution,
            "source_locator": "https://some.private.example/token?secret=LEAK"
        }]
    }

class KeyedFilesetReviewTests(unittest.TestCase):
    def test_references_keep_unknown_rights_and_no_exposed_locator(self):
        p=mod.propose_fileset(example())
        self.assertEqual(p["components"][0]["redistribution"],"UNVERIFIED")
        self.assertIsNone(p["components"][0]["source_locator"])
        self.assertNotIn("LEAK",json.dumps(p))
        self.assertFalse(p["delivery_ready"])
    def test_offline_unverified_rights_rejected(self):
        with self.assertRaises(ValueError):
            mod.propose_fileset(example(mode="PUBLIC_OFFLINE_PACK"),proven_local_hashes=["a"*64])
    def test_offline_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            mod.propose_fileset(example(mode="PUBLIC_OFFLINE_PACK",redistribution="PERMITTED"))
    def test_offline_candidate_never_claims_delivery_complete(self):
        p=mod.propose_fileset(example(mode="PUBLIC_OFFLINE_PACK",redistribution="PERMITTED"),proven_local_hashes=["a"*64])
        self.assertFalse(p["delivery_ready"])
        self.assertFalse(p["has_any_embedded_bytes"])
        self.assertFalse(p["has_signature"])
        self.assertFalse(p["receiver_cache_verified"])
    def test_private_profile_not_in_shareable_packet(self):
        x=example();x["profile_id"]="sensitive"
        with self.assertRaises(ValueError):mod.propose_fileset(x)
    def test_same_bytes_distinct_referents_dedupe_only_blob(self):
        x=example()
        x["components"].append({"source_id":"another:representation","sha256":"a"*64,"byte_length":345,"redistribution":"UNVERIFIED"})
        p=mod.propose_fileset(x)
        self.assertEqual(p["unique_blob_count"],1)
        self.assertEqual(p["source_reference_count"],2)
        self.assertEqual(p["declared_total_source_bytes"],690)
        self.assertEqual(p["declared_unique_source_bytes"],345)
    def test_same_source_duplicate_rejected(self):
        x=example();x["components"].append(dict(x["components"][0]))
        with self.assertRaises(ValueError):mod.propose_fileset(x)
    def test_same_digest_contradictory_size_rejected(self):
        x=example();x["components"].append({"source_id":"source2","sha256":"a"*64,"byte_length":346,"redistribution":"UNVERIFIED"})
        with self.assertRaises(ValueError):mod.propose_fileset(x)
    def test_manifest_hash_stable(self):
        self.assertEqual(mod.propose_fileset(example())["manifest_sha256"],mod.propose_fileset(example())["manifest_sha256"])
    def test_bad_id_and_audience_rejected(self):
        x=example();x["fileset_id"]="../escape"
        with self.assertRaises(ValueError):mod.propose_fileset(x)
        x=example();x["audience"]="FALSE_INSTITUTION"
        with self.assertRaises(ValueError):mod.propose_fileset(x)
    def test_untrusted_source_digest_rejected(self):
        x=example();x["components"][0]["sha256"]="inadequate"
        with self.assertRaises(ValueError):mod.propose_fileset(x)
    def test_registry_maintains_owner_gates_and_neutral_public_baseline(self):
        j=json.loads((REVIEW/"unispace_keyed_publication_candidate_20261020.json").read_text(encoding="utf-8"))
        self.assertIn("ISSUE_158_PUBLIC_PRIVATE_ASSET_BOUNDARY",j["activation_gates"])
        self.assertIn("ISSUE_161_SIGNED_TWO_NODE_FS_DS_CONFORMANCE",j["activation_gates"])
        self.assertEqual(j["public_bandwidth_reserve"]["kind"],"APP_QOS_POLICY_NOT_RF_CHANNEL")
        self.assertIn("RIGHTS_CONFLICT",j["merge_and_knowns"]["states"])
        self.assertEqual(j["status"],"OWNER_REVIEW_ONLY_NOT_WIRE_STANDARD_NOT_DEPLOYED")
    def test_catalogue_pinned_not_relicensed(self):
        c=json.loads((REVIEW/"alexandria_external_reference_intake_20261020.json").read_text(encoding="utf-8"))
        self.assertEqual(len(c["groups"]),2)
        for group in c["groups"]:
            self.assertEqual(len(group["records"]),group["source_lines"])
            self.assertEqual(len(group["origin"]["commit"]),40)
            self.assertTrue(all(r["rights"]=="UPSTREAM_LICENSE_UNVERIFIED" for r in group["records"]))
        self.assertEqual(len(c["historical_web"]),2)
        self.assertTrue(all(h["status"]=="CAPTURE_NOT_VERIFIED" for h in c["historical_web"]))
    def test_no_automatic_permissions_or_signature_in_plan(self):
        for mode,audience,rights in [("REFERENCES_ONLY","PUBLIC","UNVERIFIED"),("PRIVATE_OFFLINE_PACK","PRIVATE_OWNER","PERMITTED")]:
            p=mod.propose_fileset(example(mode,audience,rights),proven_local_hashes=["a"*64])
            for flag in ("delivery_ready","has_access_grant","has_signature","profile_links_disclosed"):
                self.assertFalse(p[flag])

if __name__=="__main__":
    unittest.main()
