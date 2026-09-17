# CGX Phase C Implementation Status v0.8

## Newly implemented
- UDP CGX discovery request/response baseline.
- Discovery returns identity/state/DBR/capability/service-locator information.
- TCP LAN handshake using the common CGX Connection payload.
- `lan-discover`, `lan-discovery-serve-once`, `tcp-probe`, `tcp-serve-once` CLI/reference functions.
- Object_ID allow-list verification on accepted LAN connections.
- Provider routing over a live LAN connection with measured latency.

## Proven
- Discovery is non-canonical.
- A discovered endpoint becomes canonical only after explicit `connection-add`.
- TCP connection is accepted only when the configured identity check passes.
- Remote advertised capability becomes eligible for provider routing.
- Live telemetry does not modify the canonical root.
- Both endpoint filespaces independently verify.

## Still frontier
- physical two-device/subnet validation;
- automatic broadcast/multicast discovery policy;
- signed identity and encrypted leases;
- Bluetooth, Wi-Fi Direct, WebRTC, HTTPS and connector adapters;
- resumable/chunked transfer;
- rich typed merge handlers;
- PDF/XLSX/DOCX, native Host, CCC packages, WASM/WASI, GMAT and Alexandria.

## Executable authority
The validated executable reference remains the living Drive carrier `CGX_Living_v0_8.cgx` at state S9. This branch mirrors the conformance/specification contract pending full kernel-file review/mirroring.
