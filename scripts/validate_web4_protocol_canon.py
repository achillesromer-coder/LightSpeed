#!/usr/bin/env python3
"""Validate the public-safe COIN protocol topology record.

This script deliberately validates only topology, exact dependency identity and
negative gates. It does not fetch the private/canonical archive, compile
contracts, or imply deployment, legal approval or security audit.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs" / "web4" / "COIN_PROTOCOL_CANON_2026-07-29.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_ARCHIVE_SHA256 = "fa23f1c0e193bde6d10470b00dd416da28015b7d664e58dc7eb38695c5196f1e"
EXPECTED_SOLC = "0.8.36+commit.8a079791"
EXPECTED_SOLC_WASM_SHA256 = "704877a592467d7de651ec5377ea6e3c676ae71d31f325401957d41bedfaa0d8"
EXPECTED_OPENZEPPELIN = "5.6.1"


def fail(message: str) -> None:
    raise SystemExit(f"web4 protocol canon validation failed: {message}")


def main() -> int:
    data = json.loads(RECORD.read_text(encoding="utf-8"))

    if data.get("canonical_store") != "google_drive":
        fail("canonical_store must remain google_drive")

    drive = data.get("drive") or {}
    if drive.get("readback_verified") is not True:
        fail("Drive readback must be verified")
    if drive.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256:
        fail("canonical archive checksum drift")
    if not SHA256_RE.fullmatch(str(drive.get("archive_sha256", ""))):
        fail("archive_sha256 must be 64 lowercase hex characters")
    if int(drive.get("archive_size_bytes", 0)) != 143933:
        fail("archive_size_bytes must match the Drive readback")

    assurance = data.get("private_compile_assurance") or {}
    if assurance.get("readback_verified") is not True:
        fail("private compile assurance Drive readback must be verified")
    if assurance.get("protocol_source_included") is not False:
        fail("compile-assurance topology must not contain protocol source")
    if assurance.get("public_network_authorised") is not False:
        fail("public network use is not authorised")
    if assurance.get("ephemeral_local_rehearsal_only") is not True:
        fail("only an ephemeral local rehearsal is authorised")
    for field in ("folder_id", "canonical_handoff_id", "codex_prompt_id", "receipt_contract_id"):
        if not str(assurance.get(field, "")).strip():
            fail(f"missing private compile assurance {field}")

    dependencies = data.get("dependency_baseline") or {}
    if dependencies.get("solidity") != EXPECTED_SOLC:
        fail("Solidity version drift")
    if dependencies.get("solidity_wasm_sha256") != EXPECTED_SOLC_WASM_SHA256:
        fail("Solidity compiler checksum drift")
    if dependencies.get("openzeppelin_contracts") != EXPECTED_OPENZEPPELIN:
        fail("OpenZeppelin version drift")
    if dependencies.get("foundry") != "must_be_pinned_in_private_receipt":
        fail("Foundry must remain an explicit private-receipt pin")
    if dependencies.get("forge_std") != "must_be_pinned_in_private_receipt":
        fail("forge-std must remain an explicit private-receipt pin")

    implementation = data.get("implementation") or {}
    if implementation.get("full_source_published_to_public_git") is not False:
        fail("public Git source publication is not approved")
    if implementation.get("solidity_compiled") is not False:
        fail("record must not claim a successful Solidity compile")
    if implementation.get("independent_security_audit_complete") is not False:
        fail("record must not claim an independent audit")

    gates = data.get("feature_gates") or {}
    enabled = sorted(name for name, value in gates.items() if value is not False)
    if enabled:
        fail(f"prohibited feature gates enabled: {', '.join(enabled)}")
    required_gates = {
        "production_authorised",
        "public_source_publication",
        "public_token",
        "public_sale",
        "market_listing",
        "transferable_value_rights",
        "redemption",
        "yield_or_profit",
        "customer_custody",
        "exchange_service",
        "payment_or_stored_value",
        "public_value_bridge",
        "dao_activation",
        "asset_fractionalisation",
        "autonomous_legal_commitment",
        "physical_mission_execution",
        "personal_data_on_immutable_public_ledger",
    }
    missing = sorted(required_gates - set(gates))
    if missing:
        fail(f"missing prohibited feature gates: {', '.join(missing)}")

    digest = hashlib.sha256(RECORD.read_bytes()).hexdigest()
    print(
        json.dumps(
            {
                "ok": True,
                "record": str(RECORD.relative_to(ROOT)),
                "record_sha256": digest,
                "solidity": EXPECTED_SOLC,
                "openzeppelin_contracts": EXPECTED_OPENZEPPELIN,
                "private_compile_assurance": "drive_readback_verified",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
