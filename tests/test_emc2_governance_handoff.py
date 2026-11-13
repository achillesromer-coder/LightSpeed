"""Deterministic policy checks for the bounded EMC2 governance handoff."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "governance" / "emc2_decentralised_handoff_v0_1.json"
HANDOFF_PATH = (
    ROOT
    / "docs"
    / "connector-handoff"
    / "ACR3_EMC2_DECENTRALISED_SYSTEMS_HANDOFF_2026-09-14.md"
)

EXPECTED_AUTHORITY = {
    "acr3_id": "1AgAhLPNtrO91C_-ea7EdOkOsyXrCCYvFVvmDSGq8uls",
    "type1_romer_id": "1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8",
    "owner_decision": "OD-032",
    "drive_handoff_doc_id": "1bAc2Ezj4DGlBJA8NPW2-gARpFOKHIHSQsFuVFpCT-cI",
}

REQUIRED_GATES = {
    "owner_allocation_decision",
    "rights_matrix",
    "financial_product_and_licensing_classification",
    "aml_ctf_kyc_sanctions",
    "tax_analysis",
    "corporate_equity_linkage_analysis",
    "ip_and_asset_rights_enforceability",
    "space_resource_mission_rights_analysis",
    "privacy_cybersecurity_custody_key_management",
    "smart_contract_threat_model",
    "independent_smart_contract_audit",
    "oracle_integrity",
    "consumer_investor_disclosure_and_dispute_process",
    "accounting_audit_reserve_controls",
    "explicit_owner_launch_approval",
}

REQUIRED_NO_GO = {
    "live_mint",
    "value_wallet_or_custody_setup",
    "token_sale",
    "price_or_guaranteed_valuation",
    "staking_yield",
    "liquidity_pool",
    "transferability_activation",
    "equity_or_security_claim",
    "asteroid_or_resource_title_grant",
    "revenue_share_entitlement",
    "carbon_credit_entitlement",
    "tax_instrument",
    "financial_settlement",
    "public_launch",
    "main_merge_or_deployment",
}


class Emc2GovernanceHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")

    def test_identity_state_and_authority_are_bounded(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "0.1.0")
        self.assertEqual(
            self.manifest["handoff_id"], "ACR3-EMC2-DECENTRALISED-20260914"
        )
        self.assertEqual(self.manifest["state"], "PREPUBLISH_DESIGN")
        self.assertIs(self.manifest["economic_activation"], False)

        authority = self.manifest["authority"]
        self.assertIs(authority["drive_is_canonical"], True)
        self.assertEqual(
            authority["git_role"], "bounded_implementation_review_mirror"
        )
        for key, expected in EXPECTED_AUTHORITY.items():
            self.assertEqual(authority[key], expected)

    def test_allocation_candidate_is_complete_but_not_ratified(self) -> None:
        emc2 = self.manifest["emc2"]
        allocations = emc2["allocation_candidate"]
        self.assertEqual(emc2["supply_candidate"], 100_000_000)
        self.assertEqual(sum(item["amount"] for item in allocations), 100_000_000)
        self.assertEqual(sum(item["percent"] for item in allocations), 100)
        self.assertEqual(len({item["bucket"] for item in allocations}), len(allocations))
        self.assertTrue(all(item["state"] == "DESIGN_CANDIDATE" for item in allocations))

    def test_allocation_conflict_and_equity_proposal_remain_open(self) -> None:
        emc2 = self.manifest["emc2"]
        conflict = emc2["historical_allocation_conflict"]
        self.assertIs(conflict["present"], True)
        self.assertEqual(sum(conflict["alternate_percentages"].values()), 100)
        self.assertEqual(
            conflict["required_resolution"],
            "owner_and_legal_ratification_before_contract_encoding",
        )

        equity = emc2["equity_linkage"]
        self.assertEqual(equity["source_proposal_percent_romer_equity"], 10)
        self.assertEqual(equity["state"], "PROPOSAL_NOT_EXECUTED_RIGHT")
        self.assertEqual(
            set(equity["required_resolution"]),
            {
                "executed_legal_instrument",
                "valuation_method",
                "beneficial_rights",
                "transfer_restrictions",
                "insolvency_treatment",
                "disclosure_and_enforceability",
            },
        )

    def test_governance_and_iat_are_not_live(self) -> None:
        self.assertIs(self.manifest["governance"]["live_dao"], False)
        self.assertEqual(
            self.manifest["iat"]["state"], "DISABLED_DESIGN_CANDIDATE"
        )
        self.assertEqual(
            self.manifest["evidence_pipeline"][0], "SOURCE"
        )
        self.assertEqual(
            self.manifest["evidence_pipeline"][-1], "OPTIONAL_ECONOMIC_ACTION"
        )

    def test_required_gates_and_no_go_controls_are_complete(self) -> None:
        self.assertEqual(set(self.manifest["required_gates"]), REQUIRED_GATES)
        self.assertEqual(
            set(self.manifest["no_go_without_separate_authorisation"]),
            REQUIRED_NO_GO,
        )
        self.assertTrue(
            all(
                action.startswith(
                    (
                        "resolve_",
                        "build_",
                        "refresh_",
                        "specify_",
                        "run_",
                        "prepare_",
                    )
                )
                for action in self.manifest["next_actions"]
            )
        )

    def test_handoff_document_matches_the_machine_boundary(self) -> None:
        required_phrases = [
            "PREPUBLISH DESIGN / ECONOMIC ACTIVATION DISABLED",
            "OD-032",
            "100,000,000 EMC² fixed-supply candidate",
            "50/20/20/5/5",
            "50/20/20/10",
            "remains an architectural proposal",
            "No live mint",
            "main merge or deployment",
            "Economic activation remains disabled.",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, self.handoff)
        for value in EXPECTED_AUTHORITY.values():
            self.assertIn(value, self.handoff)

        table_rows = re.findall(
            r"\| [^\n|]+ \| ([\d,]+) \| (\d+)% \| DESIGN CANDIDATE \|",
            self.handoff,
        )
        self.assertEqual(sum(int(amount.replace(",", "")) for amount, _ in table_rows), 100_000_000)
        self.assertEqual(sum(int(percent) for _, percent in table_rows), 100)

    def test_manifest_does_not_contain_secret_material(self) -> None:
        prohibited_key_names = {
            "api_key",
            "private_key",
            "secret",
            "seed_phrase",
            "mnemonic",
            "password",
        }

        def walk(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(prohibited_key_names.isdisjoint(value.keys()))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.manifest)


if __name__ == "__main__":
    unittest.main()
