# UniSpace / CGX passive edge — bounded source convergence (20 Oct 2026)

**Status:** candidate branch for owner review. Not merged, deployed, installed, paired or canonically promoted.

## Existing owner contracts retained

- `cgx/domain_templates/mobile_node_binding_contract.json`: signed mobile Host and OS grants.
- `cgx/domain_templates/node_exchange_contract.json`: distinct node IDs, source hash/size, verified receipt, leased compute.
- `plugins/source/core-skills/cgx-mobile-node/SKILL.md`: mobile bootstrap and explicit permission workflow.
- PR #174 public-only UniSpace; PR #175 R0 reference transport; PR #176 Android link; PR #178 build-only APK.
- Issues #158 (private public/static material) and #161 (true peer/FS-DS acceptance) remain blocking.

This change does not create new runtime, object store, agent, scheduler, domain or arbitrary execution tool.

## Capability profiles

| Profile | Role | Local capability | Condition for peer proof |
|---|---|---|---|
| WEB_OFFLINE | Browser-only UI | Selected-file inspection, package export, local delta | No peer claim; export candidate |
| WEB_CONNECTED | HTTPS browser surface | Operator-triggered request/view | Authenticated private server and permissions |
| ANDROID_RELAY | Secondary mobile Host candidate | Native share/intents; optional permissioned bridge | Installed keystore app, source/lease readback, independent signed host receipt |
| WEARABLE_VIA_PHONE | Watch as phone-connected peripheral | Only separately consented provider data | Never an independent compute node without own identity/process proof |
| DESKTOP_VERIFIED | Local runtime candidate | Registered deterministic tools, eligible transfer | Current authenticated node registry, signed receipt, accepted scope |

Da Fit/other companion-specific methods are **not** presumed available. Only an actually supported and user-consented provider export/OS health-data integration should be adapted; otherwise HOLD_VERIFIED_PROVIDER_ADAPTER. Treat sensor readings as sensitive and separate from public packs. No BLE snooping or app-private data access.

## Bandwidth envelope

The registry declares four *proposed upper-envelope profiles* T0–T3, with payload bounds 4 KiB / 64 KiB / 1 MiB / 8 MiB. These are conservative app limits for planning, **not measured internet bandwidth**, physical constraints or demonstrated network throughput. Payload transmission still requires approved HTTPS/peer transport, source-root verification, receiver SHA-256 readback, replay protection and lease checks. Lower-bandwidth fallback is semantic index + source references, never an invented full source.

## Source boundary

`cgx/portable_node/passive_node_plan.py` is pure stdlib, reference-only. It emits status, selected tier, capability needs, possible source digest/size, and a syntactically checked HTTPS origin. It does not:
- generate cryptographic node identity or authorization tokens;
- access Bluetooth/Health Connect/phone/watch sensors;
- connect to a host or register a peer;
- claim web-client loopback, private IP, arbitrary filesystem or device management privilege;
- enqueue compute, authorize file writes or promote canonical roots.

Do not put private source bytes, keys, credentials or health data in a bootstrap packet.

## Cross-branch merge review

- Public UniSpace PR #174 and mobile PR #176 are divergent from main; do not blindly stack their application trees.
- The latest source-only audit found issues #158 and #161 OPEN, so #172–#178 remain draft until their individual policy/acceptance gates close.
- Independently inspect `main` vs `feature/unispace-public-cgx-20261012` vs `feature/lsgo-mobile-link-20261013`, accept only identical/pre-existing code first, resolve changed-file conflicts manually and rerun focused CI.
- Source-only additive registry/plan/test branch should be evaluated independently; never auto-merge into main under live device/public release claims.

## Acceptance

Run `python -m unittest discover -s tests -p test_cgx_passive_node_plan.py -v` on this candidate branch. Then require real independent device test for Android enrollment, HTTPS owner-auth, public/private separation and signed peer readback **before** enabling DataSpace exchange or any action. Route evidence to existing #158/#161 owner lanes. This document is an additive delta, not a new lineage or execution queue.
