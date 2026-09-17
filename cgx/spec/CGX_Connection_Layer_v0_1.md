# CGX Connection Layer v0.1

Status: reference implementation proven over local IPC (Unix domain socket) in CGX Living v0.7.

## Purpose
The Connection Layer separates what the CGX needs to exchange from which transport moves it. A declared connection is canonical configuration; live availability, heartbeat, measured latency, and last-seen data are session state and MUST NOT alter the canonical content root.

## Connection descriptor
A connection descriptor may contain `id`, `type`, `locator`, `enabled`, permissions, trust, heartbeat TTL and allowed peer Object_IDs. Canonical descriptors live in `cgx/connections.json`.

## Live connection state
Live observations live under `session/` and may include online state, last-seen time, measured latency, peer Object_ID/State_ID/DBR root, advertised capabilities, transport and errors.

## Handshake
The reference handshake returns protocol version, Object_ID, State_ID, content root, DBR root, advertised capabilities and timestamp. The first transport is JSON-line request/response over a Unix domain socket.

## Routing integration
Providers may declare `connection_id`. Routing applies the existing capability/permission/trust/privacy/network gates plus connection liveness and advertised-capability checks. Measured heartbeat latency overrides static estimates when available.

## Proven
1. Local IPC endpoint advertises identity/state/DBR/capabilities.
2. Client measures live latency.
3. Session heartbeat leaves canonical root unchanged.
4. Route selection consumes live telemetry.
5. Expired heartbeat removes the provider from eligible routes.
6. Both filespaces independently verify.

## Frontier
Persistent services, Windows named pipes, LAN/Bluetooth/Wi-Fi Direct/WebRTC/HTTPS transports, signed identity, leases/encryption, chunking/resume and physical multi-device conformance.
