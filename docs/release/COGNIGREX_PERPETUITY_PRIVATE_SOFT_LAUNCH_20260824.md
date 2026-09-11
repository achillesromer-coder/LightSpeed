# Römer Industries Cognigrex Perpetuity — private soft-launch receipt

Generated: 2026-08-24 (Australia/Brisbane)

State: `STAGED_LOCAL_DERIVED`

This receipt records the bounded private local soft launch at PR #37 head
`c7b3b40b04a287d3a042a866439769632ffac25e`. It is not a public deployment,
Drive write, protected-branch merge, workbook mutation, or canonical acceptance.

## Verified local state

- LS GO bridge `http://127.0.0.1:8765/api/v1/status`: pass.
- Runtime root: `D:\LightSpeed\App` with no redirect.
- Core services: database, storage, and Merovingian available.
- Agent floors: 8 of 8 operational on the asynchronous shared queue.
- Resource guard: pass under the configured 0.5x bounded profile.
- Local frontends: loopback listeners on ports 4173 and 8081 reachable.
- Ollama: one canonical listener on port 11434; `qwen3:4b` was the bounded
  three-floor repair lane.
- PR #37: five of five reported checks passed at the recorded head.

## Database and exact-once evidence

The canonical database was opened read-only at
`D:\LightSpeed\Data\db\lightspeed_unified.db`. SQLite `quick_check` and full
`integrity_check` both returned `ok`; the stamp did not mutate the database.

- `GO-TASK-0016`: one identity row and one queue occurrence; Task 486 / Job
  490022 completed with an immutable result receipt.
- `LSGO-COGNIGREX-CYCLE-20260824-001`: one identity row and one queue
  occurrence; Task 489 / Job 490025 remain blocked. The successful bounded
  repair is separate derived evidence and did not redispatch the command,
  create a job, or rewrite the terminal identity.

Database stamp SHA-256:
`8021c3a8ea1b479289693e93fd82a80bb1654af771c88f9fa0b9c438a6191751`.

## Cleanup and recovery

Six pre-proved redundant targets (15,911,239 bytes) were removed only after
hash/directory-digest comparison and retained-counterpart validation. Recovery
backup: `D:\LightSpeed\Data\backups\redundancy_cleanup_20260824T035325Z`.
Distinct candidate trees, cache bundles, migration-preserve cascades, and
unproved `.txt` candidates were retained.

## Local publication packet

The local human and machine packet indexes 18 hashed JSON receipts:

- Human SHA-256:
  `bdf8849f9322e121988f37492d6c1122137a58ea91b256ef3bf958f02df14846`.
- Machine SHA-256:
  `08a70e6256526cd35ad1089c07acc7ab4669980ab41f7e857b2035ac2d23a23d`.

## Holds

- Public publish and Drive/workbook mutation remain held.
- PR merge has not been performed.
- RFS/EMFF empirical comparison remains evidence-gated; simulations are
  derived evidence, not empirical proof.
- De Sporte launch, Mark III mesh export, heavy simulation without the manual
  gate, and unproved destructive cleanup remain prohibited.

Next safe action: continue bounded private operation and review this receipt,
the local Perpetuity packet, and PR #37 before any canonical promotion.
