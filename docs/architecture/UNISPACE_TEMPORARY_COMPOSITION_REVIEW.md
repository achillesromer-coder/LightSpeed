# UniSpace temporary subagent composition and backend-derived surface

## Scope (18 November 2026)

One bounded source increment to the existing UniSpace/LightSpeed/Cognigrex system.
No second database, runtime, AI model, agent daemon, listener, frontend application,
mint family, DataSpace network identity or independent authority was created.

The existing `cgx_capability_registry` remains the single capability selector.
`cgx_surface_projection.py` derives the owner-scoped UI route/role palette from
the current hash-pinned registry. No hardcoded capability list is the source of
truth for that projection. The existing UniSpace System view consumes it after
owner session authentication. Existing static shell navigation is unchanged.

`plan_temporary_subagent_batch` composes registered role and route references
with existing `compose_capability_review`. It preserves source revision,
existing Task_ID and Run_ID, SHA-256 composition identity and the existing
nested ternary review root. It never copies model weights, ingests private
sources, promotes canon, schedules work, runs a capability or signs a lease.

## Bounded temporary candidate

- 1–4 distinct registered specialist role references, 1–12 registered routes.
- At most 4 proposed local CPU threads (never more than the host CPU count).
- Memory 64–1024 MiB; 1–16 jobs; declared planning TTL 60–3600 seconds.
- TTL and resource envelope are **not enforced reservations** until the current
  host scheduler and an authenticated lease apply the actual limits.
- Existing SHA-256 and ternary review packing are used. This is not evidence of
  a full T173 production codec, geometric general intelligence, or numerical
  compression improvement. T174/zero remains a non-mintable sentinel.
- Result is an immutable, deterministic review description, not a native mint,
  persisted occurrence, native signed DBR or executable delegation.

## Native gates preserved

1. Review PR #227 remains draft and source-only; its role/rights and
   metadata-only content-grant protections must be reconciled and natively
   accepted before any file-persistence installation or runtime dispatch.
2. Existing host must authenticate owner, issuer, ACL, lease, revocation,
   task identity and independent DBR readback.
3. Approve local singleton CPU/RAM concurrency and rollback within the host's
   resource guard before any subagent execution.
4. FileSpace must verify exact bytes and occurrence-specific source grants;
   cross-role matching hashes do not confer content rights.
5. DataSpace network minting is a separate future authority and peer-proof
   process. No independent node, signed exchange or consensus is inferred.
6. Native mint/public release and physical actuation remain on HOLD until
   owner-controlled qualification. Research, training and R&D expansions are
   separately gated, not silently executed or advertised as proven.

## Verification

Tests in `desktop/LightSpeed_Runtime/tests/test_cgx_surface_projection.py`
check deterministic composition, registered scope, resource caps, stale revision,
missing and gated route behavior, and HTTP unauthorized access.
The frontend type check verifies the generated surface consumption.
A running Desktop service must be restarted in an authorized maintenance
window to load the changed backend; source tests alone do not activate it.
