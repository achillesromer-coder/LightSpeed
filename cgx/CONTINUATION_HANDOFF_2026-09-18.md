# CGX Continuation Handoff — 2026-09-18

This branch is a continuity marker only. It does **not** claim runtime parity with the latest chat-proven CGX state.

## Authority split

- Latest packed/persisted runtime carrier: `/Google Drive/CGX/Phase A/CGX_Living_CURRENT_S42.cgx` (`v1.17`), 26/26 historical tests at publication.
- Latest chat-proven engineering state: **S53**, 30/30 tests after Closure-D (WASM semantic-handler bridge).
- Current work: **Closure-E / provisional S54**, topology-scoped at-rest encryption. It is unpromoted and must not be labelled implemented.

## Full handoff artifacts in Drive

- `/Google Drive/CGX/Phase A/CGX_CONTINUATION_HANDOFF_2026-09-18.md`
- `/Google Drive/CGX/Phase A/CGX_CONTINUATION_MANIFEST_2026-09-18.json`
- `/Google Drive/CGX/Phase A/CGX_NEXT_CHAT_PROMPT.txt`

## Proven post-S42 closures

- Closure-A / S45: CGX-IR Universal Cell/Basis Registry; freeze/restart/gaps governance; representation receipts; checkpoint/restore; Lens; full Inspect; H0-H3 host negotiation; offline fidelity; visualization data. 27/27.
- Operational-B / S47, corrected through S49: AI/human policy; bounded agent runtime; connector model; distributed node baseline; revocation/group-rekey/WebAuthn-reference controls. 28/28.
- Closure-C / S51: federated namespace registry reference service; deterministic CGX-P1 carrier; extension SDK. 29/29.
- Closure-D / S53: WASM-backed semantic-handler bridge. 30/30. WASI/WIT/Component Model remain unresolved.

## Duplicate-call history

A redundant promotion produced S48 after S47. S49 is the DBR-tracked undo/correction restoring the S47 canonical content. Preserve the history; do not repeat or hide the duplicate.

## Next gate — Closure-E

At-rest encryption must be implemented and tested granularly across:
whole filespace → region/surface → child CGX → individual component/payload → user/device/session → DBR/history.

Required invariants include:
- AES-256-GCM; topology scopes policy but is not itself encryption.
- secure import so plaintext never enters canonical/history storage.
- historical plaintext exposure guard for legacy data.
- no ambiguous membership in multiple encryption regions.
- child/sensitive region cannot weaken its parent's minimum factor threshold.
- per-component scope, factor threshold, history-exposure state, rekey behaviour and inheritance.
- missing/wrong factor rejection; expiring session unlock; canonical root unchanged by unlock.
- rekey can rewrap shares without re-encrypting large ciphertext where possible.
- full regression before promotion.

## Final deliverable

The user-facing product is one living `CGX.cgx`; engineering version labels/states are internal DBR lineage only.

See the Drive handoff for the complete closure frontier and successor prompt.
