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


    def test_squarespace_is_never_authority_or_private_node(self):
        p=mod.plan_unispace_surface("SQUARESPACE_PUBLIC",origin="https://romer.industries")
        self.assertEqual(p["transport_state"],"PUBLIC_EMBED_READ_ONLY")
        self.assertIsNone(p["selected_https_origin"])
        self.assertEqual(p["device_profile"],"WEB_OFFLINE")
        self.assertFalse(p["authenticated"])
        self.assertFalse(p["connection_established"])
        self.assertFalse(p["public_publish_authorized"])
        self.assertFalse(p["contains_credentials"])

    def test_sai_region_alone_does_not_activate(self):
        variants=[
            ({"jurisdiction":"AU"},"HOLD_EXPLICIT_SAI_OPT_IN"),
            ({"jurisdiction":"OTHER","sai_opt_in":True},"HOLD_AU_JURISDICTION_NOT_ESTABLISHED"),
            ({"jurisdiction":"AU","sai_opt_in":True},"HOLD_TRUSTED_AU_ELIGIBILITY_PROOF"),
            ({"jurisdiction":"AU","sai_opt_in":True,"jurisdiction_attested":True},
             "SAI_REVIEW_BY_AUTHENTICATED_SERVER")
        ]
        for params,status in variants:
            with self.subTest(params=params):
                p=mod.plan_unispace_surface("UNISPACE_APP",intelligence="SAI",**params)
                self.assertEqual(p["intelligence_eligibility"],status)
                self.assertFalse(p["sai_activated"])
                self.assertFalse(p["jurisdiction_verified_by_planner"])
                self.assertFalse(p["canonical_promotion"])
        public=mod.plan_unispace_surface("SQUARESPACE_PUBLIC",intelligence="SAI",
                                        jurisdiction="AU",jurisdiction_attested=True,sai_opt_in=True)
        self.assertEqual(public["intelligence_eligibility"],"HOLD_AUTHENTICATED_APP_REQUIRED")

    def test_natural_network_is_unproved_even_if_client_asserts_receipt(self):
        for proof in (False,True):
            p=mod.plan_unispace_surface("CGX_OWNER",transport="NATURAL_CANDIDATE",
                        natural_transport_attested=proof,
                        server_session_attested=True,origin="https://cgx.example.org")
            self.assertEqual(p["transport_state"],
                 "HOLD_NATURAL_PEER_READBACK" if proof
                 else "HOLD_NATURAL_TRANSPORT_PROTOCOL_AND_EVIDENCE")
            self.assertEqual(p["fallback_transport"],"LOCAL_OFFLINE_OR_EXPLICIT_HTTPS")
            self.assertFalse(p["natural_transport_established"])
            self.assertFalse(p["authenticated"])
            self.assertFalse(p["connection_established"])
            self.assertFalse(p["sai_activated"])

    def test_current_https_and_offline_preserve_capability_boundary(self):
        connected=mod.plan_unispace_surface("UNISPACE_APP",
                    origin="https://cgx.example.org",server_session_attested=True)
        self.assertEqual(connected["selected_https_origin"],"https://cgx.example.org")
        self.assertEqual(connected["transport_state"],"HOLD_SERVER_AUTH_AND_ACL")
        self.assertEqual(connected["device_profile"],"WEB_CONNECTED")
        offline=mod.plan_unispace_surface("UNISPACE_APP",transport="OFFLINE")
        self.assertEqual(offline["transport_state"],"LOCAL_OFFLINE_ONLY")
        self.assertIsNone(offline["selected_https_origin"])
        self.assertFalse(offline["source_bytes_embedded"])

    def test_invalid_scope_or_host_rejected(self):
        for args in ({"surface":"NATURAL_MASTER"},{"transport":"AUTO_DISCOVER_LAN"},
                     {"intelligence":"GOVERNMENT_ADMIN"},{"jurisdiction":"AUTO_GEOIP"},
                     {"origin":"http://localhost:8765"},
                     {"origin":"https://192.168.0.1"},
                     {"sai_opt_in":"yes"}):
            with self.subTest(args=args),self.assertRaises(ValueError):
                mod.plan_unispace_surface(**args)


if __name__=="__main__":
    unittest.main()
