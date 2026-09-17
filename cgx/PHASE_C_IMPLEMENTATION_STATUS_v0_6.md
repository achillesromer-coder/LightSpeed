# CGX Phase C Implementation Status v0.6

## Newly implemented and tested
- DBR ancestry comparison between independent replicas of the same Object_ID.
- Peer relation classification: identical / local-ahead / peer-ahead / diverged.
- Common-ancestor reconciliation base selection.
- Filesystem reference transport for selective changed-blob transfer.
- Peer changes staged through non-canonical branch semantics.
- Diverged JSON edits on independent fields merge and converge on both replicas.
- Different Object_ID peers are rejected before data transfer.
- Both replicas independently verify after convergence and produce the same canonical content root/topological snapshot.

## Still frontier
- Actual physical-device discovery (Bluetooth, LAN, Wi-Fi Direct, WebRTC, service connectors).
- Signed peer identity, capability leases and encrypted sessions.
- Availability heartbeat/ticker and dynamic route failover.
- Interrupted transfer resume/chunk protocol.
- General typed semantic merge handlers beyond JSON.
- Physical two-device conformance run.
