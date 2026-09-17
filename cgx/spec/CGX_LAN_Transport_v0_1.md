# CGX LAN Reference Transport v0.1

Status: reference discovery + handshake transport proven on the local IP stack in CGX Living v0.8.

## Principle
Discovery is observation, not authority. A discovered CGX endpoint is returned as a candidate containing identity, state, DBR, capabilities and a service locator. It does not become canonical filespace configuration until the host/user accepts it through `connection-add` or an equivalent policy-controlled action.

## Discovery
Reference discovery uses a small UDP request/response contract (`CGX-DISCOVERY/0.1`). The response contains:
- remote CGX handshake payload;
- advertised capability set;
- suggested service type;
- service locator, currently `tcp://host:port`.

The reference client accepts a host address explicitly. Broadcast/multicast subnet discovery can use the same message contract later.

## LAN handshake
The reference operational channel uses TCP and the same `CGX-CONNECTION/0.1` handshake established by local IPC. A canonical connection descriptor of type `lan` stores the accepted locator and policy. Live TCP observations remain under `session/`.

## Identity
A connection may pin `allowed_peer_object_ids`. The TCP probe refuses to mark the connection online when the received peer Object_ID is outside the allowed set.

## Routing
A provider can bind to the accepted connection through `connection_id`. Route selection requires a live heartbeat/capability observation and uses measured latency in the provider cost function.

## Proven
1. UDP discovery returns remote Object_ID/state/DBR/capabilities/service locator.
2. Discovery alone does not mutate canonical state.
3. The candidate can be explicitly registered as a canonical LAN connection.
4. TCP handshake verifies the expected peer identity.
5. Live remote capability becomes routable.
6. Heartbeat telemetry remains non-canonical.
7. Both endpoint filespaces verify after operation.

## Frontier
- real two-device/subnet conformance;
- broadcast/multicast policy and collision handling;
- service deduplication;
- signed discovery assertions;
- lease/encryption/session keys;
- chunking/resume/backpressure;
- NAT traversal/WebRTC;
- Bluetooth/Wi-Fi Direct transports.
