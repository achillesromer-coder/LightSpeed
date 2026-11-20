"""Negative and invariant checks for the Type-1 CGX/COIN source review."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_cgx_type1_chain_review import validate, REQUIRED, DENIED_FLAGS

REVIEW = json.loads((ROOT / "docs/web4/CGX_TYPE1_CHAIN_READINESS_REVIEW_20261111.json").read_text(encoding="utf-8"))
COIN = json.loads((ROOT / "docs/web4/COIN_PROTOCOL_CANON_2026-07-29.json").read_text(encoding="utf-8"))

class ChainReadinessReviewTests(unittest.TestCase):
    def test_readiness_pass_stays_unreleased(self):
        result = validate(REVIEW, COIN)
        self.assertEqual(result["independent_proof_gates_held"], 14)
        self.assertFalse(result["permissioned_chain_live"])
    def test_every_promotion_flag_denied(self):
        for key in DENIED_FLAGS:
            with self.subTest(key=key):
                mutated = copy.deepcopy(REVIEW)
                mutated[key] = True
                with self.assertRaises(ValueError): validate(mutated, COIN)
    def test_self_declared_proof_denied(self):
        for key in REQUIRED:
            with self.subTest(key=key):
                mutated = copy.deepcopy(REVIEW)
                mutated["required_independent_proofs"][key] = "PASS"
                with self.assertRaises(ValueError): validate(mutated, COIN)
    def test_missing_independent_peer_gate_denied(self):
        mutated = copy.deepcopy(REVIEW)
        del mutated["required_independent_proofs"]["distinct_attested_peer_hosts"]
        with self.assertRaises(ValueError): validate(mutated, COIN)
    def test_new_unregistered_root_denied(self):
        mutated = copy.deepcopy(REVIEW)
        mutated["semantic_parent"] = "CGX.cgx-new-master"
        with self.assertRaises(ValueError): validate(mutated, COIN)
    def test_early_drive_change_denied(self):
        mutated = copy.deepcopy(REVIEW)
        mutated["drive_transition"] = "CHANGE_ACL_NOW"
        with self.assertRaises(ValueError): validate(mutated, COIN)
    def test_fake_network_finality_denied(self):
        mutated = copy.deepcopy(REVIEW)
        mutated["consensus_finality"] = "DEPLOYED"
        with self.assertRaises(ValueError): validate(mutated, COIN)
    def test_coin_value_layer_disabled(self):
        mutated = copy.deepcopy(COIN)
        mutated["feature_gates"]["public_token"] = True
        with self.assertRaises(ValueError): validate(REVIEW, mutated)
    def test_coin_compile_not_assumed(self):
        mutated = copy.deepcopy(COIN)
        mutated["implementation"]["solidity_compiled"] = True
        with self.assertRaises(ValueError): validate(REVIEW, mutated)
    def test_bool_int_coercion_refused(self):
        mutated = copy.deepcopy(REVIEW)
        mutated["public_release_authorized"] = 0
        with self.assertRaises(ValueError): validate(mutated, COIN)

if __name__ == "__main__":
    unittest.main()
