# CGX Phase B Reference Kernel

This branch contains the first runnable CGX filespace kernel vertical slice. The authoritative tested carrier is `CGX_Phase_B_v0_1.cgx` in Drive under `CGX/Phase B`; Git tracks implementation source, receipts, and integration notes.

## Implemented
- ZIP-compatible `.cgx` prototype carrier.
- Separate semantic `state_root`, full `content_root`, and living `DBR root`.
- Sparse object registry and aggregate headers.
- TXT, Markdown, JSON, and CSV exact-byte payload preservation and round-trip export.
- Frontier / Overlay / Resolve lifecycle.
- Overlay isolation: uncommitted overlays do not change canonical semantic state.
- Event log plus state snapshots.
- Logical undo: a new historical event can restore an earlier semantic root.
- Deterministic semantic-parent topology with local slots.

## Not yet claimed
PDF/XLSX/DOCX rich adapters, CRDT multi-device merge, cryptographic signatures/encryption, capability leases, WASM/WASI execution, Windows host registration, CCC network registry, Alexandria resolver, or GMAT adapter.

## Authority boundary
Drive holds the tested binary carrier and receipt. This branch is the implementation/source lane. Existing LightSpeed/ACR3/Type-1 authorities remain unchanged.
