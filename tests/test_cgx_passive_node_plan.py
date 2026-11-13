"""Unit tests for source-only passive-device planning; no network or device used."""
import importlib.util
import json
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "cgx" / "portable_node" / "passive_node_plan.py"
spec = importlib.util.spec_from_file_location("passive_node_plan", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PassiveEdgeContractTests(unittest.TestCase):
    def test_profile_count_and_parent_contracts(self):
        reg = mod.registry()
        self.assertEqual(len(reg["profiles"]), 5)
        self.assertEqual(len(reg["bandwidth_tiers"]), 4)
        self.assertIn("CGX-NODE-EXCHANGE-CONTRACT/0.1", reg["parent_contracts"])

    def test_unregistered_profile_rejected(self):
        with self.assertRaises(ValueError):
            mod.plan_passive_node("WATCH_IS_FULL_NODE")

    def test_read_only_offline_browser_default(self):
        p = mod.plan_passive_node("WEB_OFFLINE")
        self.assertFalse(p["connected"])
        self.assertIsNone(p["node_id"])
        self.assertEqual(p["eligibility"], "LOCAL_CANDIDATE")
        self.assertFalse(p["authority_transfer"])

    def test_tiers_and_small_budget(self):
        self.assertEqual(mod.plan_passive_node("WEB_OFFLINE",budget_bytes=100)["chunk_bytes"],100)
        self.assertEqual(mod.plan_passive_node("WEB_OFFLINE",budget_bytes=65000)["selected_bandwidth_tier"],"T0_MINIMAL")
        self.assertEqual(mod.plan_passive_node("WEB_OFFLINE",budget_bytes=65536)["selected_bandwidth_tier"],"T1_CONSTRAINED")
        self.assertEqual(mod.plan_passive_node("WEB_OFFLINE",budget_bytes=1048576)["selected_bandwidth_tier"],"T2_STANDARD")

    def test_bad_budget_rejected(self):
        for bad in (-1,0,True,3.14,"400"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                mod.plan_passive_node("WEB_OFFLINE",budget_bytes=bad)

    def test_https_origin_only(self):
        for bad in ("http://example.org","https://localhost","https://127.0.0.1","https://192.168.0.5","https://10.0.0.4","https://user:pass@example.com","https://example.com/secret","https://example.com?token=abc","https://example.com:8443"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                mod.https_origin(bad)
        self.assertEqual(mod.https_origin("https://cgx.example.org/"),"https://cgx.example.org")

    def test_connected_browser_requires_auth_not_claimed(self):
        p = mod.plan_passive_node("WEB_CONNECTED",origin="https://cgx.example.org")
        self.assertEqual(p["eligibility"],"HOLD_SERVER_AUTH_SESSION")
        self.assertFalse(p["connected"])

    def test_android_claim_not_equivalent_peer(self):
        p = mod.plan_passive_node("ANDROID_RELAY",registered_node_proof=True)
        self.assertEqual(p["eligibility"],"HOLD_SIGNED_PEER_RECEIPT")
        self.assertIsNone(p["receipt_ref"])
        self.assertFalse(p["peer_authenticated"])

    def test_wearable_requires_permission_and_adapter(self):
        p = mod.plan_passive_node("WEARABLE_VIA_PHONE")
        self.assertEqual(p["eligibility"],"HOLD_CONSENT")
        p = mod.plan_passive_node("WEARABLE_VIA_PHONE",user_consent=True)
        self.assertEqual(p["eligibility"],"HOLD_VERIFIED_PROVIDER_ADAPTER")
        self.assertFalse(p["connected"])

    def test_source_hash_and_size_must_match(self):
        digest = "b"*64
        with self.assertRaises(ValueError): mod.plan_passive_node("WEB_OFFLINE",source_sha256=digest)
        with self.assertRaises(ValueError): mod.plan_passive_node("WEB_OFFLINE",source_sha256="bad",source_size=1)
        p = mod.plan_passive_node("WEB_OFFLINE",source_sha256=digest,source_size=9000,budget_bytes=4096)
        self.assertEqual(p["source_state"],"NOT_CACHED")

    def test_only_no_credentials_or_authority(self):
        for profile in ("WEB_OFFLINE","WEB_CONNECTED","ANDROID_RELAY","WEARABLE_VIA_PHONE","DESKTOP_VERIFIED"):
            p=mod.plan_passive_node(profile)
            self.assertFalse(p["contains_credentials"])
            self.assertFalse(p["canonical_promotion"])
            self.assertFalse(p["authority_transfer"])
            self.assertIsNone(p["lease_ref"])
            self.assertNotIn("token",json.dumps(p).lower().replace("auth_tokens","")) 

if __name__=="__main__":
    unittest.main()
