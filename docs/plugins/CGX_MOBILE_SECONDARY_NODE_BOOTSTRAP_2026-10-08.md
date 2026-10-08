# CGX Mobile Secondary Node Bootstrap — 2026-10-08

## Decision

This implementation extends the existing Cognigrex/LightSpeed topology; it does not create a mobile Cognigrex or a second runtime.

The mobile entrypoint is `cgx://cgx.cgx`. The phone is registered as a secondary node/surface, then LightSpeed GO and Achilles P.A are hydrated as bounded projections over the existing CGX authority, capability and receipt chain.

## Existing contracts reused

- `CGX-MOBILE-BOOTSTRAP/0.1`
- `CGX-DEVICE-HANDSHAKE/0.1`
- `CGX-NODE-EXCHANGE-CONTRACT/0.1`
- shared `cgx-handshake` skill
- LightSpeed GO owner command/review surface
- existing host node/root registry
- existing execution leases, transfer/compute receipts and DBR/reconciliation path

## Mobile binding

`mobile_node_binding_contract.json` defines the source-level fan-out:

```text
cgx://cgx.cgx
      |
      v
carrier/root verification
      |
      v
adaptive device handshake
      |
      v
signed mobile node identity + explicit OS grants
      |
      +----> LightSpeed GO : operator command/review/status
      +----> Achilles P.A  : oversight/release gate
      +----> providers     : Drive/Git/etc via existing connectors
      +----> BouwerBase    : peer node when independently online/proven
      +----> mobile-local  : only registered, lease-bound capabilities
      `----> other CGX    : lazy selector/capability hydration
```

No subsystem is duplicated onto the phone merely because it becomes reachable.

## Android physical gate

A `.cgx` file is a carrier/entrypoint, not an Android privilege token. Full mobile integration therefore requires a Host implementation (native Android or a bounded PWA plus native adapter) that physically registers the open/share/deep-link path, creates a keystore-backed node identity, requests individual user permissions, and returns signed capability readback.

Until exercised on the handset, Android file-handler registration, keystore assurance, two-device discovery/sync and independent mobile compute remain NOT_PROVEN.

## Intended acceptance sequence

1. Install/register mobile Host.
2. Open/share a verified Cognigrex carrier or `cgx://cgx.cgx` link.
3. Verify content root and current Recovery lineage.
4. Generate/restore keystore-backed node key.
5. Request selected Android capabilities.
6. Register signed capability envelope with CGX host registry.
7. LSGO loads mobile projection; Achilles oversight binds.
8. Execute one harmless registered mobile capability.
9. Return signed receipt/readback.
10. Exercise mobile <-> BouwerBase exchange when BouwerBase is independently online.
