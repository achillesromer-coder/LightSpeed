from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "probe_cgx_launch_empirical.py"
CONTRACT = ROOT / "cgx" / "domain_templates" / "launch_empirical_preflight_contract.json"

spec = importlib.util.spec_from_file_location("cgx_launch_empirical_probe", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class LaunchEmpiricalPreflightTests(unittest.TestCase):
    def test_receipt_never_closes_empirical_gates_from_single_host(self) -> None:
        receipt = module.build_receipt(
            source_head="a" * 40,
            host_class="windows",
            node_identity={
                "supported": True,
                "method": "fixture-sha256",
                "node_fingerprint_sha256": "b" * 64,
                "raw_identifier_persisted": False,
            },
            ipv4_count=1,
            credential_probe={
                "supported": True,
                "provider": "fixture",
                "synthetic_only": True,
                "production_credential_touched": False,
                "secret_in_receipt": False,
                "write_readback_pass": True,
                "revocation_delete_pass": True,
                "post_revocation_absent": True,
                "cleanup_verified": True,
                "production_integration_verified": False,
                "recovery_path_verified": False,
            },
        )

        self.assertEqual(receipt["launch_007"]["state"], "EMPIRICAL_OPEN_PREPARED")
        self.assertFalse(receipt["launch_007"]["distinct_peer_verified"])
        self.assertFalse(receipt["launch_007"]["closure_claim"])
        self.assertEqual(receipt["launch_008"]["state"], "EMPIRICAL_OPEN_PREPARED")
        self.assertTrue(receipt["launch_008"]["synthetic_host_boundary_pass"])
        self.assertFalse(receipt["launch_008"]["production_integration_verified"])
        self.assertFalse(receipt["launch_008"]["recovery_path_verified"])
        self.assertFalse(receipt["launch_008"]["closure_claim"])
        self.assertFalse(receipt["authority_transfer"])
        self.assertFalse(receipt["canonical_promotion_authorized"])
        self.assertFalse(receipt["public_publish_authorized"])

    def test_contract_forbids_secret_and_raw_host_identifiers(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        forbidden = set(contract["receipt_rules"]["restricted_or_forbidden"])
        for field in (
            "raw_machine_guid",
            "hostname",
            "ip_address",
            "mac_address",
            "username",
            "password",
            "session_token",
            "credential_blob",
            "recovery_secret",
            "private_key",
        ):
            self.assertIn(field, forbidden)
        self.assertIn(
            "one physical host never satisfies the two-distinct-device predicate",
            contract["invariants"],
        )
        self.assertIn(
            "synthetic credential tests never prove production credential integration",
            contract["invariants"],
        )

    def test_receipt_json_has_no_secret_value_slots(self) -> None:
        receipt = module.build_receipt(
            source_head=None,
            host_class="test",
            node_identity={
                "supported": False,
                "method": "test",
                "node_fingerprint_sha256": None,
                "raw_identifier_persisted": False,
            },
            ipv4_count=0,
            credential_probe={
                "supported": False,
                "provider": "test",
                "synthetic_only": True,
                "production_credential_touched": False,
                "secret_in_receipt": False,
                "write_readback_pass": False,
                "revocation_delete_pass": False,
                "post_revocation_absent": False,
                "cleanup_verified": True,
                "production_integration_verified": False,
                "recovery_path_verified": False,
            },
        )
        serialized = json.dumps(receipt).lower()
        for forbidden in (
            "raw_machine_guid",
            "hostname",
            "ip_address",
            "mac_address",
            "\"password\"",
            "session_token",
            "credential_blob",
            "recovery_secret",
            "private_key",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
