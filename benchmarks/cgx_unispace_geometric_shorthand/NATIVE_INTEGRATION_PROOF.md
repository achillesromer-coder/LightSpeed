# CGX UniSpace R0 × FileSpace × Node Exchange — bounded integration proof

**Status:** Review-only candidate. No live peer admission, no hosted runtime change, no signed lease, no canonical mutation. Existing `Cognigrex.cgx`, native provider/file revisions and DBR roots remain authoritative.

## Implemented
- `node_exchange_r0_adapter.py` — verifies actual source bytes against a supplied native identity and revision **claim**, compares complete raw, ordinary ZIP-DEFLATE and R0-CGXS full carriers, optionally considers root-bound sparse updates when a matching baseline is supplied to a local fixture.
- `reconstruct()` verifies carrier digest, source bytes and final source SHA-256; forbids ZIP multi-entry/path traversal, output overrun, cache mismatch and unexpected modes.
- `native_node_transfer_plan()` imports **the existing** `lightspeed_runtime.node_exchange.build_transfer_envelope` and constructs a **planned** envelope from an already-staged and readback-verified candidate. The envelope addresses the wire carrier, while a separate field retains the original source root. It cannot mint a lease or call `execute_local_transfer`.
- All forms of `provider_revision_attested`, `acl_attested`, `lease_validated`, `peer_transport_verified`, `canonical_promotion_authorized`, `physical_actuation_authorized` are explicitly false. A metadata string is not proof of provider authenticity.

## CI
[CGX R0 integration test workflow](https://github.com/achillesromer-coder/LightSpeed/actions/runs/38214420691) passed **17 existing tests + 13 native-adapter tests**. It also executed source→carrier→receiver CLI readback, failed closed without a prior root and ran portable fuel-for-fuel fixtures.

[Local expanded adapter kit](https://drive.google.com/file/d/1yfI1nuwRClw3NJTaWepctI0vU4MP1v22/view) additionally exercises an independent Python receiver process on one machine, but that is **not** evidence for a second authenticated device.

## Measured additional source corpus (local model container; carrier payload only)

| Test | Source B | Selected cold carrier | Cold B | Controlled one-byte warm update B |
|---|---:|---|---:|---:|
| Structured JSON | 35,579 | ZIP-DEFLATE | 3,406 | 531 |
| Pseudorandom bytes | 262,144 | raw | 262,144 | 530 |
| Original Freedoom Phase 1 WAD | 28,795,076 | ZIP-DEFLATE | 10,305,037 | 536 |
| Tested playable DOOM HTML | 22,018,509 | ZIP-DEFLATE | 16,588,032 | 535 |
| Starter DOOM ZIP | 25,244 | ZIP-DEFLATE | 23,781 | 531 |

Exact source SHA-256 equality was verified after reconstruction. Warm edits are artificial one-byte modifications and were not executed as games. Network frame/manifest, signatures, recipient installation cost, electricity/joules, target machine performance, real peer reliability and source licences are **not** included. Control metadata is nonzero even when a no-change candidate carries zero data bytes.

## Release gates before activation
1. Current native provider revision, owner ACL, licence and registry root verified by **existing** host adapters; claimed metadata alone must fail closed.
2. Signed, scoped Node Exchange admission and lease; authorise safe carrier transport separately from source read permissions and output writes.
3. Two independent devices, authenticated peer connection and failure/replay/resume checks, with transport bytes and physical measurements.
4. At destination, compare exact source/native revision, stage output, inspect conflicts and require separately authorised owner mutation/DBR readback.
5. Benchmark against ZIP, bsdiff/xdelta and zstd with *same* transport framing, cold-cache cost and device energy measurements. Keep existing public/private gate #158 and interoperability gate #161.

**No architecture duplication:** This is an optional byte/geometry reference codec under the existing FileSpace/Node Exchange system, not a semantic R1 decoder, a second DataSpace, or a public LS GO upload endpoint.
