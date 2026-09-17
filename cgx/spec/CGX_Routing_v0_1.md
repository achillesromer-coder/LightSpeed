# CGX Provider Routing v0.1

## Purpose
Provider routing converts a resolved dependency/capability requirement into a bounded choice of where and how it should be obtained or executed. Dependency planning answers *what* is required. Routing answers *which declared provider/connection* should satisfy it.

## Provider contract
A provider descriptor minimally carries an ID, capability list, connection types, locator, enabled state, trust, permissions and route-cost attributes. Connection types are transport/capability hints such as `local-ipc`, `filesystem`, `bluetooth`, `lan`, `webrtc`, `https`, `api`, or later registered transports. They do not themselves grant control authority.

## Hard gates
A candidate is rejected before scoring if any mandatory gate fails: capability, enabled state, minimum trust, required permission, privacy bound, or allowed network/connection class.

## Cost function
The v0.1 reference router ranks surviving candidates from weighted terms for latency, transferred bytes, compute cost, privacy penalty, semantic/topological distance, and authority/evidence penalty. Weights are policy data in `cgx/route_policy.json`, not constants hard-coded into the object model.

## Security rule
Discovery is not authority. A found device or endpoint must still expose a compatible signed/approved capability adapter and pass the active CGX lease/policy before execution.

## Next extension
Actual discovery and transport adapters remain frontier: Bluetooth/LAN/WebRTC/API/IPC discovery, availability heartbeat, workload execution receipts, and adaptive re-routing.
