# S88 corpus-aware child-shell status — 2026-09-21

The first corpus-aware Römer/Eco/EMASSC base shells were regenerated from a fresh clone-required reader seed against S88/v1.58.

## S88 reference
- carrier SHA-256: `e901bb175152eed0b1ceb9cf69fc464bc433e4a37d725c01343cea42151d356f`
- state: S88
- tracked canonical master objects: 416
- isolated regression reported by S88 handoff: 71/71 PASS
- carrier verifier during shell build: PASS

## Hydration proof during shell build
Reader hydration: PASS
- 57 entries
- 725,172 bytes
- stack root `d08d989d7ef3d6ab61bc2bf4c0243f1b0e7098709f87544e164195ac791db3a3`
- seed verification remained PASS

Runtime hydration: FAIL CLOSED
- `master-proof-rejected:hydration-entry-not-in-manifest`
- the previously observed canonical-core / `cgx/topology_index.json` proof mismatch therefore persists in S88.

No child-shell workaround was added.

## Authority boundary
ACR3 currently records visible packed Recovery authority at S53 while S88 is a later Validation descendant. The domain shells record both and explicitly refuse promotion by State_ID alone. ACR3 retirement remains gated on ancestry/content reconciliation and explicit authoritative promotion/readback.

## Corpus-aware shell rule
The child shell may contain source maps, workbook topology, domain-specific ACR3 migration metadata, current bounded provider snapshots, work-mode/tool/lens configuration and first-file queues. It must not bulk-copy unrelated project or personal payload merely to appear complete.
