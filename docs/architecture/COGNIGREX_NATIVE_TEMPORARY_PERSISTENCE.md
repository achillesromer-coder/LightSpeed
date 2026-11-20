# Native Cognigrex temporary persistence — host-owned activation contract

## Goal and actual scope

Implement bounded **review-state persistence** in the existing LightSpeed
operational database without creating another canonical store, runtime,
agent process, scheduler, FileSpace content grant or DataSpace identity.

The implementation uses `OperationalStore.record_event` and the existing
`operational_events` table in `lightspeed_unified.db`:
- `cgx_temporary_checkpoint_review_v1` records one deterministic, task/run
  keyed, source-revision-bound subagent composition candidate
- `cgx_temporary_checkpoint_revoke_v1` revokes that candidate without
  deleting historical records
- SHA-256 readback verifies the exact stored event and candidate identity
- the first persisted event timestamp anchors a fixed TTL (60–3600 seconds);
  idempotent retries never extend it
- expired or revoked records remain available as evidence, never executable

## Authentication and write gate

Only an **owner session verified by the existing Desktop bridge**, with its
current private review authority contract, can call the write endpoint.
No legacy owner-confirmation header fallback or unauthenticated role label
can call the new persistence routes. The request must regenerate the
composition from the existing pinned CGX selector; any unknown or gated
capability is rejected. All content-rich source retrieval and learning
remain outside this bounded metadata-only contract.

Three owner-session endpoints are added to the existing bridge:

- `POST /api/v1/cgx/persistence/checkpoint`: accepts the same exact task,
  run, source revision, role/route and budget arguments as the existing
  temporary-batch planner; persists a *review-only* checkpoint.
- `GET /api/v1/cgx/persistence/checkpoint/{task_id}/{run_id}`: returns
  exact receipt metadata, fixed expiry and effective revoked/expired state.
- `POST /api/v1/cgx/persistence/revoke/{task_id}/{run_id}`: accepts only
  `expected_candidate_sha256`, writes an append-only revocation event.

**No actual CPU reservation, subagent dispatch, byte-level source hydration,
model training, signed DBR, mint, rights promotion or off-device transfer.**
A stored review candidate is not a compute lease. The T173/T174 research
catalogue and ternary review root have not been admitted as a native codec.

## Operational acceptance

1. Live Desktop bridge on BouwerBase reports healthy database, storage and
   Merovingian supervisor; native operator queue-index and representation
   edge remain held by their independent gates.
2. Read-only check confirms canonical `operational_events` and
   `operational_routes` already exist; no schema migration or second
   database is required. The adapter fails closed if they are missing.
3. Unit and authenticated HTTP tests must pass for forged tokens, authority
   gate, recovery, idempotency, TTL, tamper detection, privilege flags, exact
   rollback/revocation and scope isolation.
4. Existing Bridge regression, capability tests and frontend typecheck pass.
5. The live service is **not restarted automatically**. The previously
   identified service stop-window/rollback gate remains necessary before
   activating changed endpoints on port 8765.
6. For first live acceptance, the actual owner signs in via the private
   UniSpace UI, stages a non-sensitive test task/run, confirms event readback
   after a supervised restart, then revokes it. Only after that evidence can
   this sub-capability be marked LIVE.

## Next expansion (not silently authorized)

- Map FileSpace per-occurrence content grants through the host's authenticated
  LOAD and ACL layer, with denied-by-default legacy grant migration and
  independent rights evidence.
- Connect review checkpoints to the existing host scheduler with enforceable
  CPU/RAM reservations and separately issued `COMPUTE_ONLY` leases.
- Attach provider/model-weight registry and reversible inference state only
  after independent tests show no cross-source leakage and resource regression.
- Keep the DataSpace network mint a separate issuer and peer-verified
  authority. Public release, external execution and physical actuation
  retain their own gates.

## Rollback

Revert the reviewed source commit if necessary and restart only within an
authorized maintenance window. The feature writes no new schema. Persisted
checkpoint events remain immutable historical entries; use the authenticated
revocation endpoint to make a checkpoint inactive rather than deleting
operational evidence. Older consumers ignore the new event kinds.
