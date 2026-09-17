# CGX Phase B Implementation Status v0.2

Superseded as the current living-carrier status by `cgx/PHASE_B_IMPLEMENTATION_STATUS_v0_4.md` while retained for lineage.

## Implemented in the original v0.2 reference kernel
- `cgx create`, `inspect`, `verify`, `import`, `export`, `frontier`, `overlay`, `resolve`, and ZIP-compatible carrier read/write.
- TXT, Markdown, JSON and CSV baseline adapters.
- overlay exclusion from canonical content root.

## Later living-carrier increments
v0.3 added semantic-locality topology, blob-backed path deltas, true new-state undo and context-sensitive CGX addressing. v0.4 added dependency-closure/geodesic pull planning and nested CGX child composition modes. See the v0.4 status/spec files on this branch; executable code mirror review remains separate from living-carrier proof.
