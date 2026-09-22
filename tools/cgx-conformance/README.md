# CGX conformance operational index

This directory is a public operational index for the CGX field-conformance programme.

## Current authority reference

- Object_ID: `cgx:phase-a:42d99b46c0d322f08b59b7b7`
- Recovery state: `S89`
- Release: `v1.59`
- Carrier SHA-256: `dfdcc27b0002c960e81426b9dc14059bdf20b0ca864964bde5461ec6867d5f31`
- Current field execution: `CGX-PHY-20260922-BNE-04`
- Field status: `PREPARED` — external physical evidence remains pending.

S89 was promoted into Recovery by exact-content/DBR ancestry reconciliation from Recovery S53 after an independent 72/72 isolated regression pass. The canonical carrier and implementation remain on the controlled CGX Drive surfaces and are **not mirrored into this public repository**.

The earlier S88 field runbook is retained here as provenance. `CURRENT.json` and the S89 runbook identify the active field execution.

This repository surface intentionally contains only:
- stable identity/hash metadata;
- public operational run instructions;
- PREPARED field-run metadata;
- the applicable evaluation licence.

It does not contain private node keys, credentials, mutable field receipts, unpacked carrier source, the proprietary `.cgx` carrier, or a second canonical authority.

## Claim boundary

A GitHub commit, CI run, local process pair, VM pair, container pair, cloud copy, remote desktop session, or Drive transfer does not close the CGX physical-device gate.

The field gate can close only after two genuinely distinct physical devices run the required direct non-loopback test-plane scenarios, independently sign their node receipts, converge to equal final roots, and pass the existing CGX field-receipt validators.

## Standards alignment

The current CGX field contract uses TLS 1.3 and zero-trust identity semantics:
- RFC 9846 — TLS 1.3: https://www.rfc-editor.org/rfc/rfc9846
- NIST SP 800-207 — Zero Trust Architecture: https://csrc.nist.gov/pubs/sp/800/207/final

Local-network presence grants no authority by itself.

Copyright © 2026 Nathaniel C N Bouwer. All rights reserved.
