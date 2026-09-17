# CGX Phase B Implementation Status v0.2

## Implemented in the reference kernel
- `cgx create` for empty filespace directories.
- `cgx inspect` aggregate/root/frontier inspection.
- `cgx verify` content-root and DBR verification.
- `cgx import` for TXT, Markdown, JSON and CSV profiles with raw preservation and semantic sidecars.
- `cgx export` exact payload projection.
- `cgx frontier` listing.
- `cgx overlay` ephemeral overlay creation excluded from canonical content root.
- `cgx resolve` controlled overlay promotion to canonical state with DBR event.
- ZIP-compatible `.cgx` carrier read/write.

## Proven in the living carrier test suite
- TXT exact byte round-trip.
- JSON canonical semantic hash.
- Overlay non-mutation of canonical content root.
- Resolve changes canonical state/root.
- DBR/content-root verification after mutation.

## Explicitly unresolved
- Locality-preserving recursive quadtree/Hilbert topology kernel.
- Content-addressed immutable blob store and semantic event deltas.
- True `cgx undo` based on reversible state deltas.
- Nested CGX aggregation.
- Deterministic 3D Topological Snapshot geometry.
- PDF/XLSX/DOCX adapters.
- OS host integration, CCC packages, sync, WASM, security leases and Alexandria.
