# S87 hydration gate — observed during domain skeleton build

## Reference master

- Carrier: `CGX_Parallel_S87_MobileAdaptiveHandshake_v1_57.cgx`
- Expected carrier SHA-256: `0988bbe834602c911191a73a66872ad3ec9eb2564afa8dfd707c51273edc4c8c`
- S87 handoff: 408 tracked canonical objects; 70/70 isolated regression PASS.

## Skeleton-build observation

A current seed template was generated through the S87 hydration API and instantiated into fresh domain workspaces.

**Reader hydration:** PASS
- profile: `reader`
- mode: `cache`
- entries: 55
- selected master bytes: 708,388
- hydrated stack root: `f31830cbb168a1e5211542426370a627f013b58494d0c9b05501723047516067`
- seed verification remained PASS.

**Runtime/developer hydration:** FAIL CLOSED

The distribution proof advertises:

`cgx/topology_index.json`

inside the `canonical-core` layer, but that control file is not present in the canonical manifest used by the hydration proof.

Observed reason:

`hydration-entry-not-in-manifest`

Observed path:

`cgx/topology_index.json`

## Boundary

This branch does not weaken or bypass the proof. Domain skeletons therefore use the proven `reader` hydration baseline. Work modes may declare runtime/developer as requested targets, but must surface the gate until the master distribution/manifest contract is reconciled.

Candidate correction belongs in the CGX master lineage, not in each child template.
