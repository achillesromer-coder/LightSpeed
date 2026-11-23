#!/usr/bin/env python3
"""Fail-closed hosted-to-native acceptance preflight for existing UniSpace.

A hosted FileSpace/DataSpace interface, model selector, native checkpoint
metadata, synthetic CI or public Git PR is not proof of an independently
signed native/peer DBR. This module accepts an ephemeral input report but
never stores it, verifies private keys, grants a lease, writes canonical
state, deploys, mints, starts agents or operates devices.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "CGX-UNISPACE-NATIVE-ACCEPTANCE-PREFLIGHT/0.1"
ROOT = "cgx:root:cognigrex"
GATE_SCHEMA = "CGX-UNISPACE-CROSSSPACE-GATE-REGISTRY/0.1"
HOSTED_SCHEMA = "cgx.lightspeed-go.handshake/1"
HEX64 = re.compile(r"^[a-f0-9]{64}$")
GATE_ID = re.compile(r"^[A-Z]+-[0-9]{2}$")
MAX_GATES = 64
MAX_INPUT = 128_000
ACTIONABLE_PRIORITY = (
    "US-01", "IM-01", "FS-01", "DS-02", "FS-02", "DS-01",
    "FS-03", "DS-03", "US-03", "US-04",
)


class NativeAcceptanceHold(ValueError):
    """Hosted/native proof cannot be accepted or is malformed."""


def _str(v: Any) -> bool:
    return isinstance(v, str) and bool(v) and len(v) <= 400


def _gate_set(gates: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if (not isinstance(gates, dict) or gates.get("schema") != GATE_SCHEMA
            or gates.get("canonical_root") != ROOT or gates.get("source_count") != 51):
        raise NativeAcceptanceHold("original one-root 51-gate register not qualified")
    items = gates.get("task_groups")
    if not isinstance(items, list) or len(items) != 51:
        raise NativeAcceptanceHold("original gate list not complete")
    keyed: dict[str, dict[str, Any]] = {}
    for row in items:
        if (not isinstance(row, dict) or not isinstance(row.get("id"), str)
                or not GATE_ID.fullmatch(row["id"]) or row["id"] in keyed
                or row.get("state") != "OPEN_REVIEW_ONLY"
                or row.get("owner_approval_observed") is not False
                or row.get("effectful_action_authorised") is not False
                or not _str(row.get("label"))
                or not isinstance(row.get("proposed_dependencies"), list)):
            raise NativeAcceptanceHold("gate identity, closure state or owner permission invalid")
        keyed[row["id"]] = row
    for item in keyed.values():
        deps = item["proposed_dependencies"]
        if (len(deps) != len(set(deps)) or item["id"] in deps
                or any(not isinstance(d, str) or d not in keyed for d in deps)):
            raise NativeAcceptanceHold("missing or duplicated gate dependency")
    pending = {n: set(row["proposed_dependencies"]) for n, row in keyed.items()}
    ordered: list[str] = []
    while pending:
        ready = sorted(k for k, deps in pending.items() if not deps)
        if not ready:
            raise NativeAcceptanceHold("cyclic native acceptance dependencies")
        ordered.extend(ready)
        pending = {k: deps - set(ready) for k, deps in pending.items() if k not in ready}
    if len(ordered) != 51:
        raise NativeAcceptanceHold("incomplete gate order")
    return keyed


def _hosted_claim(hosted: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(hosted, dict) or hosted.get("schema") != HOSTED_SCHEMA:
        raise NativeAcceptanceHold("missing signed-in hosted handshake schema")
    if hosted.get("parent") != ROOT or hosted.get("profile") not in ("LOAD.Lite", "LOAD"):
        raise NativeAcceptanceHold("foreign root or unsupported LOAD profile")
    identity = hosted.get("identity")
    capabilities = hosted.get("capabilities")
    authority = hosted.get("authority")
    desktop = hosted.get("desktop")
    if (not isinstance(identity, dict) or not isinstance(capabilities, dict)
            or not isinstance(authority, dict) or not isinstance(desktop, dict)
            or not _str(identity.get("provider"))
            or type(identity.get("authenticated")) is not bool
            or not _str(identity.get("scope"))
            or not _str(desktop.get("state"))
            or not _str(desktop.get("reportedAt"))):
        raise NativeAcceptanceHold("incomplete hosted identity/desktop disclosure")
    expected = ("nativeAdmitted", "executionAuthorized", "canonicalWrite", "authorityTransfer")
    if any(type(authority.get(field)) is not bool for field in expected):
        raise NativeAcceptanceHold("unknown native authority claims")
    if any(capabilities.get(k) not in ("hosted", "held", "unverified", None)
           for k in ("filespace", "dataspace", "native", "peer")):
        raise NativeAcceptanceHold("unrecognized source carrier state")
    # These claims are presentation metadata, never verified identity/DBR.
    return {
        "hosted_session_authenticated_claim": identity["authenticated"],
        "hosted_filespace_available_claim": capabilities.get("filespace") == "hosted",
        "hosted_dataspace_available_claim": capabilities.get("dataspace") == "hosted",
        "native_admitted_claim": authority["nativeAdmitted"],
        "canonical_write_claim": authority["canonicalWrite"],
        "native_execution_claim": authority["executionAuthorized"],
        "desktop_report_state": desktop["state"],
        "desktop_reported_at": desktop["reportedAt"],
        "independent_peer_verified": False,
    }


def assess(gates: dict[str, Any], hosted: dict[str, Any]) -> dict[str, Any]:
    """Always returns a *review* report, never an authority promotion."""
    keyed = _gate_set(gates)
    view = _hosted_claim(hosted)
    zero_dependency = sorted(k for k,v in keyed.items() if not v["proposed_dependencies"])
    priority = [key for key in ACTIONABLE_PRIORITY if key in keyed]
    ordered = []
    for gate_id in priority:
        row = keyed[gate_id]
        ordered.append({
            "id": gate_id,
            "name": row["label"],
            "depends_on": list(row["proposed_dependencies"]),
            "status": "OPEN_REQUIRES_INDEPENDENT_NATIVE_EVIDENCE",
            "original_owner_approval_observed": False,
        })
    if not {"US-01", "IM-01", "FS-01", "DS-02"} <= set(zero_dependency):
        raise NativeAcceptanceHold("root evidence-preflight dependency chain changed")
    result = {
        "schema": SCHEMA, "root": ROOT,
        "state": "NATIVE_AND_PUBLIC_RELEASE_HELD",
        "original_gate_count": len(keyed),
        "source_observation": view,
        "zero_dependency_review_gates": zero_dependency,
        "priority_sequence": ordered,
        "admission_requirements": [
            "INDEPENDENT_CURRENT_NATIVE_HOST_IDENTITY_AND_OWNER_ACL",
            "SIGNED_LEASE_ISSUER_TRUST_NONCE_REVOCATION",
            "FILESPACE_R0_BYTES_AND_SCOPED_HYDRATION_HASH_READBACK",
            "DATASPACE_SIGNED_DBR_ATOMIC_APPEND_AND_COLD_RESTART_READBACK",
            "INDEPENDENT_TWO_NODE_PEER_RECOVERY_PROOF",
            "NO_PRIVATE_BYTES_IN_PUBLIC_GUI_OR_BUILD",
            "RIGHTS_LICENCE_RELEASE_SIGNOFF_AND_VERIFIED_ROLLBACK",
        ],
        "note": ("Even a forged or future hosted nativeAdmitted:true flag cannot "
                 "replace an independent owner-key verification and host/peer readback."),
        "source_gate_registry_mutated": False,
        "independent_native_signature_verified": False,
        "native_admitted": False,
        "canonical_write_approved": False,
        "model_training_executed": False,
        "mint_authorized": False,
        "production_deploy_authorized": False,
        "peer_recovery_verified": False,
    }
    result["review_sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",",":"), ensure_ascii=True,
    ).encode()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-register", type=Path, required=True)
    parser.add_argument("--hosted-handshake", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.gate_register, args.hosted_handshake):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT:
            raise NativeAcceptanceHold("missing/oversize hosted review source")
    gates = json.loads(args.gate_register.read_text("utf-8"))
    raw = json.loads(args.hosted_handshake.read_text("utf-8"))
    if isinstance(raw, dict) and isinstance(raw.get("structuredContent"), dict):
        raw = raw["structuredContent"]
    print(json.dumps(assess(gates, raw), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
