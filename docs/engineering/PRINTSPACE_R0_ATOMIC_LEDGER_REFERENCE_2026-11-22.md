# PrintSpace R0 atomic challenge ledger interface — 22 Nov 2026

## Convergence / authority boundary

This increment extends `apps/lightspeed-go/src/printspaceR0SignedEvidence.mjs`
in the existing LightSpeed/UniSpace CGX R0 lane, **not** a separate CGX root,
new production database, persistent scheduler, native DBR or machine control
plane. This module is a host-supplied `consumeNonce` contract and a temporary
SQLite reference used only for regression. No real owner keys, source bodies,
production ACLs, host clock attestations or native machine permissions are
added. This does not mean the owner DataSpace is connected or authorised.

## Contract and execution ordering

1. `reviewPrintspaceR0WithAtomicLedger(caseInput, ledger)` runs the existing
   three-independent-role Ed25519 R0 proof verifier. Any malformed signature,
   revoked signer, expired time, wrong product/source/rights, trust pin, or
   scope is `HOLD` *before* invoking the ledger.
2. For a valid **review-only** proof, it passes only a SHA-256 nonce digest,
   reviewed receipt digest, source facet content address, plan digest and
   expiry to `ledger.consumeNonce(request)`. It does not transmit a raw
   challenge, private signing key, material source bytes, native DBR receipt,
   machine command or operational lease.
3. A host implementation **MUST** perform a single atomic globally unique
   insert and return the exact `CGX-PRINTSPACE-R0-NONCE-INSERT-ACK/0.1` shape.
   `INSERTED` produces `REFERENCE_LEDGER_INSERTED_REVIEW_ONLY` and
   `ALREADY_PRESENT` produces `HOLD`, with no fallback to a local Set or
   stale negative-only history hints. Any error, missing adapter, timeout or
   schema/receipt mismatch produces `HOLD`.
4. An `INSERTED` acknowledgement is *not authenticated by this library*.
   `owner_trust_root_authenticated`, `host_ledger_independently_authenticated`,
   `challenge_consumption_authoritative`, `native_admitted`, `machine_authorised`,
   `mint_authorised` and `native_dbr_written` stay **false**, even when all
   signatures and a reference insert pass. This deliberately separates the
   mathematical atomic-insert result from independently accepted host authority.

## Reference implementation and reproducibility

`scripts/printspace_r0_sqlite_reference_ledger.py` uses SQLite's existing
transaction/unique-key mechanisms as a **test-only** reference; it does **not**
create a production DB. `init` sets WAL journaling and creates a local table
with a primary key on the *global* nonce digest. `consume` validates a strict,
small JSON payload, opens a separate connection, executes `BEGIN IMMEDIATE`,
`INSERT OR IGNORE`, then commits. Its `FULL` synchronous and busy-timeout
settings are for this local reference. There is deliberately no automatic
nonce deletion, time-based replay exemption, or raw secrets in the stored
rows. A real host must supply backup/recovery, retention, independently
verified time, signed append-only audit and revocation receipts.

The production-grade host store is **not** created or changed by this PR.
The user-authorised host must independently attest the trust-root origin,
per-child ACL, source registry byte readback, rights/collision checks, and
atomically consume nonce challenges across all replicas. DBR/mint and any
physical C0/toolpath remain separate sign-off processes.

## Regression scope

- Independent restart and per-process SQLite connections: same nonce accepts
  once; later calls `ALREADY_PRESENT` across batches.
- Concurrent workers and signed cross-product challenges: one global winner
  for a repeated nonce; independent nonces all accept into reference table.
- Forged/expired signatures never call the ledger. Unavailable/malformed host
  acknowledgement always holds; even a fake `INSERTED` response grants no
  native authority.
- A bounded Python smoke suite runs in the existing sequential PrintSpace
  regression. LightSpeed GO Vitest also runs end-to-end signer/reference tests.
- All results are **synthetic digital software verification**, not empirical
  machine production, authenticated owner storage, or commercial release.
