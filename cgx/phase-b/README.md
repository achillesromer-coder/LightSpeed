# CGX Phase B Reference Kernel

This branch contains the first runnable CGX kernel vertical slice. The authoritative Phase-B carrier remains the `.cgx` package in Drive; Git tracks the implementation source, tests, and design notes.

Implemented: create, inspect, verify, import/export for TXT/Markdown/JSON/CSV, sparse object registry, aggregate headers, Frontier/Overlay/Resolve, event log, semantic state root, package root, DBR root, and logical undo.

Not yet claimed: rich PDF/XLSX/DOCX adapters, multi-device merge, signatures/encryption, WASM/WASI execution, Windows host integration, CCC remote registry, Alexandria resolver.
