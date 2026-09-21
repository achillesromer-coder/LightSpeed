# CGX conformance operational index

This directory is a public operational index for the CGX field-conformance programme.

## Current authority reference

- Object_ID: `cgx:phase-a:42d99b46c0d322f08b59b7b7`
- Validation state: `S88`
- Release: `v1.58`
- Carrier SHA-256: `e901bb175152eed0b1ceb9cf69fc464bc433e4a37d725c01343cea42151d356f`
- Current field execution: `CGX-PHY-20260921-BNE-03`
- Field status: `PREPARED` — external physical evidence remains pending.

The canonical carrier and reference implementation are distributed separately through the controlled CGX Drive validation surface. They are **not mirrored into this public repository** because CGX is currently distributed under the CGX Proprietary Evaluation Licence v1.0.

This repository surface intentionally contains only:
- stable identity/hash metadata;
- public operational run instructions;
- PREPARED field-run metadata;
- the applicable evaluation licence.

It does not contain private node keys, credentials, mutable field receipts, unpacked carrier source, or a second canonical authority.

## Claim boundary

A GitHub commit, CI run, local process pair, VM pair, container pair, cloud copy, or Drive transfer does not close the CGX physical-device gate.

The field gate can close only after two genuinely distinct physical devices run the required direct non-loopback test-plane scenarios, independently sign their node receipts, converge to equal final roots, and pass the existing CGX field-receipt validators.

## Standards alignment

The current CGX field contract uses TLS 1.3 and zero-trust identity semantics:
- RFC 9846 — TLS 1.3: https://www.rfc-editor.org/rfc/rfc9846
- NIST SP 800-207 — Zero Trust Architecture: https://csrc.nist.gov/pubs/sp/800/207/final

Local-network presence grants no authority by itself.

Copyright © 2026 Nathaniel C N Bouwer. All rights reserved.
