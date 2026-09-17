# CGX Peer Sync v0.1

## Purpose
Peer Sync is the first transport-backed reconciliation proof for independent CGX replicas. The reference transport is a locally addressable filesystem path; it deliberately exercises the same object/state/DBR contract that later Bluetooth, LAN, WebRTC, HTTPS or connector transports can carry.

## Handshake/status
Peers first compare Object_ID. Different objects are rejected before state transfer. Compatible peers compare current DBR ancestry and classify the relationship as identical, local-ahead, peer-ahead, or diverged. The latest common DBR root is the reconciliation base.

## Delta pull
For peer events after the common ancestor, the receiver derives the touched paths and earliest Base metadata, then transfers only the desired/current blobs needed for those paths. Full filespace copies are not required.

## Merge
Transferred changes are staged as a non-canonical peer branch and use the same Base / Current / Proposed merge engine. JSON independent-field changes merge; conflicting same-field changes remain explicit conflicts.

## Proof boundary
The v0.1 test uses two independent local filespace copies and filesystem transport. It proves transport-independent sync grammar and selective blob transfer, not physical-device discovery, cryptographic session establishment, leases, availability heartbeat, or lossy/interrupted network recovery.
