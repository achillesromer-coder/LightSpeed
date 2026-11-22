# PrintSpace CGX -> existing UniSpace host R0/LOAD preflight

**Status:** `IMPLEMENTED_DIGITAL_REVIEW_ONLY`, **not** native `FileSpace` admission, signed rights, physical PrintCeptor operation, or commercial release.

## Scope and canonical source

This incremental adapter lives inside the existing `achillesromer-coder/LightSpeed` PrintSpace review branch/PR #236. It reads the source-bound `CGX-PRINTSPACE-FILESPACE-BUNDLE/0.1` (80 indexed content-addressed digital facets) and replays its source against `printspace_virtual_factory_catalog_v0_1.json`. No new CGX root, owner registry, material database, scheduler, LOAD service, assistant, crypto signing key, or authoritative rights table is established.

**Names are deliberately separate:**

- `cgx://printspace/` is the existing **digital shorthand/display namespace**; its `product/diode`, `product/board`, and `product/phone` aliases are **not** native semantic `Object_ID`s.
- `Cognigrex.cgx` is the declared parent. The existing UniSpace host R0 context gate currently recognises `Romer.cgx` as a child; this bridge does **not** invent or register a new `PrintSpace.cgx` top-level child.
- `LOAD.cgx` remains a library alias/source-review plan and cannot be minted as a root or used as an execution service merely by receiving a handoff.

## Implemented functional path

1. `printspace_cgx.check_bundle` verifies graph hashes, dependency closure, source-catalogue pin, 80-object identity and digital-only limits. `printspace_host_preflight.prepare_r0_host_review` additionally **recompiles the exact canonical bundle from the original catalogue** before preparing any review.
2. The default `printspace_host_r0_review_v0_1.json` contains **three product facet bindings with no candidate native IDs**. `h0_handshake` contributes zero source-byte hydration, no DBR receipt and no admission.
3. Optional explicit `product_bindings` may name one untrusted *candidate* semantic ID/twin and source registry/lineage blob SHA-1 strings per product, to prepare a future host-context request. It rejects duplicate semantic IDs, wrong child domain, malformed SHA-1s, unexpected authority fields, embedded tokens, unbounded or noncanonical objects and changed source pins. These syntactically shaped values are never treated as independent provider readback.
4. `apps/lightspeed-go/src/printspaceCgxHostR0Bridge.mjs` composes the **existing** `projectCgxHostObjectContextGate` and `projectUniSpaceLoadLens`, not replacements. It verifies the expected hash-pinned review plan and exact product-facet selection and refuses mismatching child/twin/host responses. It returns only metadata approved for an R0 *review plan*. It **does not** fetch, authenticate, hydrate private data, sign, mint, install agents or publish. Its separate `trustPins` parameter must originate in a trusted host configuration to have any evidentiary value; a caller furnishing both plan and pins cannot self-attest.
5. `verify_r0_host_review_back_down` recomputes from original source objects to detect drift in bundle identity, product aliases, candidate bindings and all authority fields. It explicitly returns `PASS_DIGITAL_ONLY` or `HOLD`.

## Host-governance and genuine admission gate

The existing UniSpace adapters currently return `PLAN_ONLY_NOT_HYDRATED`. Their `source_registry_independently_verified`, `host_context_readback_authenticated`, `native_admitted` and `private_hydration_authorized` fields remain **false**, even if caller metadata claims “rights cleared for review.” The crosswalk therefore does **not** grant H1-H4 private hydration, R1-R3/F layers, actual ACLs, signed DBR, minted Object_ID or device control. The authentic host must provide independent: source registry and lineage byte/hash readback; unique semantic identity/collision review; owner rights and licence; permitted user/session and child ACL; accepted parent DBR receipt; and explicit revocation semantics. **No fixture has those facts.**

## Validation

- Python regression: source replay, no-ID default, unique candidates, collisions, altered source, private fields, nonfinite/overbudget request, false authority and canonical build fixture.
- Node interoperability regression: real existing UniSpace `cgxHostObjectContextGate.mjs` and `cgxLoadLibraryLensPlan.mjs`, three product selectors, changed hash pins, wrong FileSpace, revoked client, collision, private fields, activation and simulated host execution attempts.
- Existing sequential PrintSpace regression runner extends by **one** bounded source-only suite. Existing 23-stage coverage continues and no native or machine commands are invoked.
- CI execution is required before this review draft is mergeable. A software success does not turn the synthetic registry candidates into accepted real native IDs.

## Next acceptance inputs

Current owner-approved source registry, actual lineage and canonical Object_ID readback, authoritative rights/ACL and negative revocation tests, DBR gate and native H0/H1 lease semantics; after that separately verified machine CAD, tool calibration, material passports, real coupons and environmental/functional acceptance. The next physical execution remains under independent C0 and cannot be activated from this plan.

Remote Desktop Commander is not used for this increment (normal reserve 25%, emergency floor 24%). No archive/deletion, DBR mutation, minting or publication has been performed.
