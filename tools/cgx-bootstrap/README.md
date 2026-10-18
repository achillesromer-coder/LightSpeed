# CGX minimum local bootstrap (review candidate)

This adds a command-line bootstrap to the existing LightSpeed repository; it is not another CGX server, scheduler or remote-desktop service.

## Local use (Node.js 20+)

From an existing trusted local checkout:

    node tools/cgx-bootstrap/bin/cgx.mjs discover
    node tools/cgx-bootstrap/bin/cgx.mjs observe --samples 3 --interval-ms 1000
    node tools/cgx-bootstrap/bin/cgx.mjs seed
    node tools/cgx-bootstrap/bin/cgx.mjs seed --write alexandria.public.cgx

For a local native command without fetching a registry package:

    npm install -g ./tools/cgx-bootstrap
    cgx discover
    cgx seed

Or use `cd tools/cgx-bootstrap && npm test` without installation.
The package is **private**, source-only and **not published** to the npm registry.
Do not use `npx @cognigrex/cgx@latest` until its release and scope ownership are verified.
`@.cgx` is a human shorthand, not a complete `@scope/package` npm specifier.

## Discovery contract

`discover` first makes a read-only GET to the existing bridge's native `http://127.0.0.1:8765/api/v1/cgx/bootstrap` public advertisement. If that endpoint explicitly returns 404, it falls back to the older `http://127.0.0.1:8765/api/v1/status` for backward-compatible detection. It uses loopback only, a fixed 2-second timeout per bounded probe, no redirects and a 64 KiB response cap. A returned advertisement is never a signed device admission or restored session.
Returned information excludes local filesystem paths, usernames and credentials.

- `BRIDGE_RESPONSIVE_ONLY`: status candidate, **not** Smith consumer/queue execution proof.
- `BRIDGE_PRESENT_DEGRADED`: bridge responds but status unhealthy.
- `LOCAL_BRIDGE_UNREACHABLE_OR_UNTRUSTED`: the probe failed; **not** proof the PC is offline.
- `observe`: 1–5 bounded samples, no daemon, persisted session or queue execution.

The existing execution route remains LS GO UI -> authenticated bridge -> canonical DB/queue -> Smith LSGoJobConsumer -> leased typed action -> independently read-back receipt.
Bridge `/api/v1/status` currently does not verify the Smith consumer heartbeat.
That check belongs in the existing bridge/consumer (PR #159), not in a second worker.

## Public `.cgx` seed

`seed` prints a versioned, UTF-8, JSON public skeleton with a dimensionless dodecahedron: 20 reference vertices, 30 edges, 12 neutral face cells.
It preserves distinctions among free, unknown, withheld, neutral, occupied, reserved, conflict and proposed growth.
It contains **no real source data, trusted content root, private geometry mesh, signing credential or installed-device authority**.
`seed --write` explicitly creates a new `.cgx` filename only in the current folder; rejects traversal and protected Documents; never overwrites an existing file.
Changing the extension does not make arbitrary content an admitted CGX FileSpace object.

## Next authenticated device-network acceptance

1. Verify a real local installed CGX process, its source hash, OS-keystore device identity and actual consumer heartbeat.
2. Explicitly enroll a trusted peer using mutually authenticated HTTPS or a separately approved authenticated relay; pin peer identity.
3. Use a short-lived challenge, replay prevention, a scoped lease and verified permissions, never a public geometric mnemonic as a secret.
4. Negotiate registered dictionary, version, geometry, valid previous source root, cache coverage and authorised sparse deltas.
5. Submit one harmless typed task through the existing queue; obtain fresh ACK, execution result and independent receipt readback.
6. Test stale consumer/lock, offline, duplicate, changed context, replay, path traversal and revocation.

**No** network listener, LAN scan, Wi-Fi AP, VPN, GPS, radio backscatter, telemetry, public tunnel, remote command execution or credential restoration is enabled by this CLI.
Remote ChatGPT cannot reach a PC's loopback address merely because LS GO is open locally.
Protect C:/Documents and configured user Documents; preserve existing C:\Cognigrex and D:\LightSpeed roots.

**Evidence ceiling:** source-only npm-compatible CLI. Not installed on BouwerBase, not published to npm, not a live persistent handshake, not an authenticated second CGX node.
