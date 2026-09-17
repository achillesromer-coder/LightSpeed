# CGX Phase B Kernel Implementation v0.1

## Implemented
- Standard-library Python reference kernel.
- `create`, `inspect`, `verify`, `import`, `export`, `frontier`, `overlay`, `resolve`, `undo` in the tested carrier.
- Immutable SHA-256 payload blobs for imported TXT/Markdown/JSON/CSV.
- Semantic/state root distinct from package/content root.
- Sparse object registry and aggregate headers.
- Frontier overlays that do not mutate canonical state until resolve.
- Event log and per-state snapshots for logical undo.
- Deterministic semantic-parent + local-slot topology path.

## Not yet implemented
- PDF/XLSX/DOCX/HTML rich adapters.
- CRDT/semantic multi-device merge.
- Signatures/encryption/capability leases.
- WASM/WASI runtime.
- CCC remote package registry.
- Alexandria resolver.
- Windows host/file association.

## Root model
`state_root` identifies active semantic state. `content_root` identifies the complete carrier history/payload state excluding generated bootstrap/manifest/DBR files. Undo can reproduce an earlier `state_root` while producing a new DBR/content root because history has advanced.

## Tested carrier
Drive: `CGX/Phase B/CGX_Phase_B_v0_1.cgx`.
