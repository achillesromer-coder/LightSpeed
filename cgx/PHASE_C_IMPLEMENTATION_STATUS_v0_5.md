# CGX Phase B/C Implementation Status v0.5

## Newly implemented and tested
- Provider/capability registry baseline.
- Policy-driven provider routing with hard capability/trust/permission/privacy/network gates.
- Cost ranking over latency, transferred bytes, compute, privacy, semantic distance and authority penalty.
- Explicit TRACK child refresh retaining Object_ID continuity.
- Non-canonical branch creation/staging backed by immutable blobs.
- Three-way merge grammar (Base / Current / Proposed).
- Field-aware JSON semantic merge for independent changes.
- Explicit same-field conflict detection; no silent last-write-wins.

## Retained proofs
All v0.2-v0.4 kernel behaviours remain: raw/semantic import, verification, DBR, Frontier/Overlay/Resolve, topology/index/snapshot, new-state undo, contextual addressing, nested child modes, and geodesic dependency planning.

## Still frontier
- Actual network/device discovery and transport execution.
- Two-device sync over a real connection.
- General typed semantic merge handlers beyond JSON.
- Availability heartbeat and dynamic route re-selection.
- Cryptographic capability leases/signatures on providers/children.
- PDF/XLSX/DOCX adapters, native Host, CCC registry/runtime, WASM, GMAT and Alexandria.
