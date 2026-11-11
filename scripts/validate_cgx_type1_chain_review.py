#!/usr/bin/env python3
"""Fail-closed non-networking source-level Type-1 CGX/COIN readiness review.

PASS only verifies that unproven authority and consensus remain HELD.
It does not verify a signature, a real independent peer, deployed Solidity or finality.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA = "CGX-TYPE1-CHAIN-READINESS-REVIEW/0.1"
COIN_ID = "coin-protocol-canon-2026-07-29"
NODE_SCHEMA = "CGX-NODE-EXCHANGE-CONTRACT/0.1"
REQUIRED = frozenset({
    "accepted_root_and_object_ids", "source_rights_and_acl",
    "installed_runtime_parity", "signed_issuer_and_revocation",
    "valid_lease_and_downstream_enforcement", "distinct_attested_peer_hosts",
    "authenticated_peer_exchange", "interrupted_resume_hash_readback",
    "replay_and_rollback_rejection", "fork_conflict_and_finality_rules",
    "independent_dbr_receiver_readback", "unispace_permissioned_save_reopen",
    "private_static_route_negative_tests", "source_archive_compile_and_security_review",
})
DENIED_FLAGS = frozenset({
    "drive_link_access_is_private", "production_network_deployed",
    "native_dbr_finality_verified", "public_release_authorized",
    "value_layer_authorized", "authority_transfer_by_copy",
    "canonical_root_replacement_authorized",
})

def validate(review: dict, coin: dict) -> dict:
    if not isinstance(review, dict) or not isinstance(coin, dict):
        raise ValueError("review and COIN records must be JSON objects")
    if review.get("schema") != SCHEMA or review.get("status") != "SOURCE_REVIEW_ONLY":
        raise ValueError("review schema or status invalid")
    if review.get("existing_coin_record") != COIN_ID or coin.get("record_id") != COIN_ID:
        raise ValueError("existing COIN identity mismatched")
    if coin.get("canonical_store") != "google_drive":
        raise ValueError("existing COIN source-of-truth changed")
    if review.get("semantic_parent") != "Cognigrex.cgx":
        raise ValueError("second or changed semantic root refused")
    if review.get("node_exchange_contract") != NODE_SCHEMA:
        raise ValueError("unrecognised node exchange contract")
    if review.get("network_class") != "PROPOSED_PERMISSIONED_RECEIPT_NETWORK":
        raise ValueError("network class overstated or changed")
    if review.get("consensus_finality") != "NOT_SPECIFIED_OR_PROVEN":
        raise ValueError("consensus/finality claim requires independent proof")
    if review.get("drive_transition") != "KEEP_EXISTING_SHARING_UNTIL_INDEPENDENT_DATASPACE_REPLACEMENT_ACCEPTED":
        raise ValueError("unapproved Drive transition")
    for key in DENIED_FLAGS:
        if review.get(key) is not False:
            raise ValueError(f"ungrounded promotion or action: {key}")
    requirements = review.get("required_independent_proofs")
    if not isinstance(requirements, dict) or set(requirements) != REQUIRED:
        raise ValueError("required independent proof matrix incomplete or changed")
    if any(value != "HOLD" for value in requirements.values()):
        raise ValueError("source-only reviewer cannot promote an independent proof")
    feature_gates = coin.get("feature_gates")
    if not isinstance(feature_gates, dict) or not feature_gates:
        raise ValueError("COIN prohibited feature gates missing")
    if any(value is not False for value in feature_gates.values()):
        raise ValueError("existing COIN value/public gates must remain disabled")
    implementation = coin.get("implementation")
    if not isinstance(implementation, dict):
        raise ValueError("COIN implementation proof missing")
    for key in ("full_source_published_to_public_git", "solidity_compiled", "independent_security_audit_complete"):
        if implementation.get(key) is not False:
            raise ValueError(f"unsupported COIN implementation assertion: {key}")
    if not isinstance(review.get("non_equivalence"), list) or len(review["non_equivalence"]) < 6:
        raise ValueError("non-equivalence controls missing")
    actions = review.get("prohibited_automatic_actions")
    if not isinstance(actions, list) or len(actions) < 7:
        raise ValueError("automatic-action refusal controls missing")
    return {
        "source_review": "PASS",
        "independent_proof_gates_held": len(REQUIRED),
        "permissioned_chain_live": False,
        "native_mint_proven": False,
        "cryptographic_finality_proven": False,
        "public_release_authorized": False,
        "drive_permissions_changed": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--coin", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(
            json.loads(args.review.read_text(encoding="utf-8")),
            json.loads(args.coin.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"TYPE1_REVIEW_HOLD: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
