# CGX Phase B Implementation Status v0.4

The living `.cgx` carrier has advanced through v0.4 and validates at State S5. This Git branch currently contains the earlier v0.2 Python reference kernel plus the v0.3/v0.4 specifications; the executable v0.4 kernel is canonical in the living carrier pending code-mirror review.

## Proven in the living carrier
- semantic-locality topology index and deterministic Topological Snapshot hash;
- immutable blob-backed DBR path deltas and new-state undo;
- context-sensitive `.cgx`, `object.namespace.cgx`, `folder.cgx/`, `cgx:` and `cgx://` interpretation;
- explicit dependency closure and hydration ordering;
- nested CGX child descriptors for EMBED, REFERENCE, PIN and TRACK;
- embedded child Object_ID/content-root verification.

## Next frontier
- network source-selection cost routing;
- TRACK refresh and semantic multi-user merge;
- rich PDF/XLSX/DOCX adapters;
- native host, CCC registry, WASM/WASI, GMAT, leases and Alexandria.
