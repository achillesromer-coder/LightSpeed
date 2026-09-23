# LS GO Physical Operations Starter — implementation contract

Date: 2026-09-23
Branch: `feature/physical-operations-starter-2026-09-23`

## Purpose

Add an evidence-gated physical-operations progression layer to the existing LS GO command centre without replacing its queue, bridge, representation graphs, or canonical routing.

The front surface must answer:
1. What am I physically building now?
2. What is the next executable action?
3. What tools/materials/manuals apply?
4. What evidence closes this step?
5. What does it unlock?
6. What is blocked and what is the smallest unblock?
7. Where is the canonical source?

## Integration contract

- `apps/lightspeed-go/public/physical-operations-seed.json` is a **seed/projection**, not canonical authority.
- LS GO task/result receipts remain the operational task ledger.
- Google Calendar owns scheduled execution time.
- Drive owns designated manuals/evidence.
- Git owns code/spec/runtime.
- CGX remains the canonical object/state/proof layer as it becomes callable.
- Existing LS GO command-centre behavior must remain functional.

## UI order

`HOME / TODAY / MAP / BUILD / TEST / OUTREACH / LIBRARY / ACHILLES`

Home must prioritize:
- Current Level
- Next Physical Action
- Current Gate
- Blocker
- Required Evidence
- Unlocks

Do not expose the whole roadmap by default.

## Gate semantics

A level may transition to PASSED only if:
- prerequisites are satisfied;
- close criterion is satisfied;
- required evidence exists and is readable;
- no unresolved safety gate invalidates execution.

Failure/rework is valid progress when evidence removes uncertainty.

## First pilot

Campaign: Bootstrap Laboratory
Current level: L0 Operating Baseline

First field mission:
- photograph current workshop/lab/shed;
- record dimensions and utilities;
- inventory tools/instruments/materials;
- record hazards and blockers.

Close only when a reviewer can identify what is physically executable next without guessing.

## Implementation next

1. Sites builder consumes this seed and existing handoff document.
2. Current LS GO UI adds additive physical-operations navigation/cards.
3. Field input initially routes to bounded manual/queue paths.
4. Then connect Calendar, Drive, Git and CGX read projections.
5. Authenticated writes remain bounded and receipt-producing.

## Safety / claims

Render state distinctly:
PLANNED / SIMULATED / BUILT / OBSERVED / MEASURED / REPEATED / INDEPENDENTLY VERIFIED / CERTIFIED.

Never promote simulated/calculated work to empirical proof.
