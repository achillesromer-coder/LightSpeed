# CGX PrintSpace R0 — bounded signed-review batch and regression sweep

**Status:** source-only digital review. No native FileSpace/LOAD admission, owner trust root, authenticated clock, persistent challenge ledger, rights approval, DBR, physical printer, mint, or commercial release.

## Single-engine insertion

`apps/lightspeed-go/src/printspaceR0BatchSweep.mjs` orchestrates the existing `verifyPrintspaceR0SignedEvidence` verifier in deterministic case order. It does **not** duplicate the signature checks, UniSpace host gate, LOAD gate, root scheduler, or archive DB. The existing Ed25519 verifier still requires three signatures (registry, rights, host) against separately supplied public-key pins, binds product facet and exact R0 source and checks expiry/revocation claims. The batch projection **does not** authenticate supplied public-key pins, host clock, source registry, licence or revocation evidence.

The bounded input schema `CGX-PRINTSPACE-R0-BATCH-REVIEW/0.1` is `{schema, cases, known_consumed_nonce_sha256}`. Each case is `{request, trust_pins, clock_seconds}`. The immutable output enumerates only index, non-privileged hold code and hashed nonce, and for valid reviews product ID and signed review hash. No public-key PEM, raw challenge, signature, secret or source bytes are returned. The batch cap is 512 cases and 8 MiB of JSON input. All conditions are fail-closed.

## Deterministic sweep and replay semantics

- Verify each independently signed non-repeated challenge; a successful Ed25519 review is **`SIGNATURES_VALID_REVIEW_ONLY`**, never admitted, minted or machine-authorised.
- Detect and deny repeated 256-bit nonces **within the same batch**, even for different products; a denied or invalid signature does not consume a nonce.
- An optionally supplied list of historical nonce SHA-256s can conservatively deny a known repeat. These are **untrusted negative-only hints**, not evidence of a durable, race-safe or independently authenticated host ledger.
- The review result hash is deterministic for identical batch input. `replayPrintspaceR0Batch` recompiles the batch and detects any altered decision, ordering, nonce or false authority. The result cannot prove persistence or independence of its own inputs.
- Strictly malformed input and extra privilege properties HOLD; an invalid case does not stop other cases. All native DBR/rights/device fields remain false.

## Tested coverage

Synthetic in-memory signing keys are generated only during Vitest and are not stored in code or artifacts. Tests cover the diode/board/phone scope, roles and fingerprints inherited from the existing verifier; within-batch nonce collision and cross-product replay; tampered signed statement, forged trusted history, invalid clock, unexpected properties, 512-case limit, 256-case mixed valid/rights/epoch/expiry sweep, full replay of original input, negative authority assertions, and deterministic output.

The 256-case synthetic sweep consists of 64 valid R0 signature-review cases, 64 tampered product-ID statements, 64 changed revocation epochs, and 64 expired-clock cases. It is **not** a real-world throughput or reliability sample. No physical or in-situ manufacturing claim is inferred from execution time.

## Next original evidence gates

The host must issue challenges using cryptographically secure randomness, verify the owner-approved trust registry, reject revoked public keys, authenticate the live host clock and source registry/licences, and perform atomic one-time nonce consumption with durable read-after-write, distinct across workers and replicas. Product-level ACL and signed DBR approval remain independent. Only independently verified real PC01 CAD, tool positioning, C0, material lots, witness coupons and measurements can advance physical PrintSpace. These are **not** implemented by this bounded review-batch layer.

**Operational policy:** retain a single canonical implementation in `LightSpeed` draft PR #236; use existing Vitest and component-atlas CI, no new scheduled coordinator; protect 25% normal / 24% emergency RDC reserve; no local machine or remote desktop commands.
