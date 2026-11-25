# CGX persistence-family native ABI reconciliation — 18 November 2026

**Decision: SOURCE COMPATIBLE; NATIVE ADMISSION HOLD.**
This is a reproducible source preflight, not a signer, loader, installer,
new database, native execution lease, model-weight training run, or mint.

## Verified source lineage

- Existing local operator checkout: `ops/canonical-queue-index-20261115`,
  committed parent `498e89dc5291aff8694fb555693eb35086fc0c91`.
- Draft persistence-family review: [PR #227](https://github.com/achillesromer-coder/LightSpeed/pull/227),
  exact review head `028f34e856cc011346beb2a0ff9d5d7f0ef45257`.
- Draft's pinned baseline: `0376a7330f02adfc1a6c928f5428cc8df3082f63`,
  verified an ancestor of the current local branch.
- Three exact source contracts, compared to the draft's own embedded pins:
  - `achilles/operator.py`: `385a1ea3b1a531b32226486d0a7d6b8494efdafc`
  - `node_exchange.py`: `80f677fec0e197cbb54a0339a7155b7becedf29b`
  - `execution_lease_contract.json`: `637de5a3b904b5df0e865dd8f9477b3e7750c3d7`
- All three native source contracts retain their required callable/field shapes.
  Windows CRLF checkouts differ from Git's LF blob bytes; use `git hash-object
  --path <relative> --stdin` without writing objects to verify canonical
  Git-cleaned content and detect genuine edits. Raw mismatch is not, by itself,
  evidence of a source code change.

## What the audit explicitly does not establish

The draft family's `FamilyStore` owns `family.sqlite3`. It must NOT be
launched or merged as a competing operational database. Its specialist
`content_granted` occurrence method set exists in the draft source, but is
not Windows/LOAD ACL authentication, not an authorized cross-Grex read and
not native DBR or evidence promotion.

The current authenticated host must provide an adapter for:
1. Per-occurrence identity, content permission, rights, revocation and source
   provenance, including fail-closed migration of legacy unknown grants.
2. Pinned task/run IDs, host-backed lease, issuer, ACL, independent signed DBR
   replay, reversible rollback and exact source revision readback.
3. One host scheduler with CPU/RAM reservations, a singleton controller,
   heartbeat, stop authority and negative tests.
4. Cross-domain projections that reuse exact content only when permission
   scopes overlap; never infer scientific equivalence from matching hashes.
5. Separate off-device DataSpace node identity and independently proven
   authenticated transport; do not mint a network from a local runtime.

The `CGX-UNISPACE-DYNAMIC-SURFACE/0.1` and
`CGX-TEMPORARY-SUBAGENT-BATCH-REVIEW/0.1` source additions remain
non-executing, backend-derived review descriptions. T173 codec performance
and AGI capabilities remain unverified; T174/zero is not mintable.

## Repeatable read-only check

The exact review head must already be fetched into the local Git object
database; no network requests occur in the preflight itself.

```powershell
$env:PYTHONPATH = 'D:\LightSpeed\Repositories\LightSpeed_Canonical\desktop\LightSpeed_Runtime'
D:\LightSpeed\Environment\Scripts\python.exe -m lightspeed_runtime.cgx_persistence_preflight --repo D:\LightSpeed\Repositories\LightSpeed_Canonical --strict-parity
D:\LightSpeed\Environment\Scripts\python.exe -m pytest D:\LightSpeed\Repositories\LightSpeed_Canonical\desktop\LightSpeed_Runtime\tests\test_cgx_persistence_preflight.py -q
```

Acceptance is **source compatibility only**. Do not restart the Desktop
bridge, install the draft family SQLite store, start background workers,
grant unrestricted filesystem access, merge PR #227, mint CGX, publish a
release, or declare DataSpace peer proof based on this check.

## Next operational gate

The least-risk next increment is a **read-only adapter contract** mapping
per-occurrence grants and lineage to the existing authenticated FileSpace/
LOAD/DBR authority, tested with both positive and negative fixtures. Only
after independent auth, migration and rollback proof should native
temporary persistence be activated.
