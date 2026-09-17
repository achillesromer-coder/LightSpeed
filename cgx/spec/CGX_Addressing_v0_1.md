# CGX Addressing and Context Semantics v0.1

CGX intentionally reuses the token `cgx` in different syntactic positions so a host can infer intended use before hydrating payload data.

- `object.cgx` — portable carrier / resting filespace.
- `object.namespace.cgx` — carrier with a human namespace hint; authoritative identity remains Object_ID + signed namespace record.
- `folder.cgx/` — mounted or expanded filespace boundary; children inherit the boundary until another explicit filespace boundary is crossed.
- `cgx:namespace:object` — logical object address independent of transport.
- `cgx://namespace/object` — resolver/network address; transport is negotiated by the host.
- `/cgx/...` in a web route — web-shell route convention, not a distinct object identity.
- Nested `*.cgx` objects are child filespaces and retain independent identity.

Position is semantic metadata, not security. The host must verify bootstrap, namespace record, DBR and permissions after discovery.
