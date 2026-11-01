# Achilles P.A / CGX — owner-operator profile and route handoff (2026-11-01)

**State:** public-safe source-only review; not minted, installed, approved, deployed or released.

## Existing owners / components — do not replace

Achilles is the owner's persistent personal assistant and cross-domain evidence/operations overseer, not a second Neo, scheduler, local model service or semantic root. Current role and domain ownership from agent_role_reconciliation.md:
- Achilles owns EMASSC and canonical/source/rights/assurance/release oversight.
- Neo owns Romer-Grex operational routing and existing LightSpeed floor execution.
- Athene owns Eco-Grex intelligence and subject evidence.
- Cognigrex.cgx is current parent, semantic ID cgx:root:cognigrex; UniSpace is permissioned R3 presentation.

The proposed friendly names Achilles.AI.Romer.cgx and AI.Achilles.Romer.CGX are unminted aliases, NOT a transfer from EMASSC to Romer ownership. A future CGX.cgx root redesign requires separate authorised migration.

Reuse in place:
- desktop/LightSpeed_Runtime/lightspeed_runtime/achilles/operator.py — existing AchillesOperator.
- desktop/Desktop_Hooks/LightSpeed/Z Axis/Z+2_Neo/ai/achilles_assistant.py and achilles_context.py — earlier assistant/context.
- desktop/Desktop_Hooks/LightSpeed/Z Axis/Z+3_Trinity/ui/achilles_dock.py — local model-facing dock.
- desktop/LightSpeed_Runtime/lightspeed_runtime/cognigrex_supervisor.py — Neo-supervised bounded workflows.
- local_floor_runner.py, agentic_launch_queue.py and ls_go_job_consumer.py — existing model, queue and receipt paths.
- scripts/run_cgx_agent_runtime.py — existing assurance and execution envelope, not independent cryptographic issuer verification.
- plugins/packages/achilles — selector and handshake, not a new runtime.

## Source ladder and evidence provenance

Early Achilles AI Development, GPT Integration, Task Executor, Achilles P.A, and October 2026 audit conversations are privately indexed from the complete twelve-shard export. No private conversation content is copied into public Git.

Drive P.A primary references:
- LS_GO_Queue_2026_07_07: historical GO task, ownership, approval and receipt entries; historical workbook statuses are not live host proof.
- CGX-LightSpeed Chat Handoff (2026-10-05): C:\Cognigrex source FileSpace, D:\LightSpeed operational receipts.
- Achilles P.A CGX Frontier Cohesion Lens (2026-10-21): cross-domain shared properties require explicit validity models; no conflation of analogy with empirical proof.
- ACHILLES Independent Governance Closure (2026-10-30): R0 original bytes/rights, R1 reversible parse, R2 typed relations, R3 permitted presentation, no self approval and signed DBR/lease gates.

The existing review/cgx-achilles-bouwerbase-stage35-20261101 branch is a separate pinned-source host-acceptance workstream. This change does not mutate its tested tree or assert host readback.

## Narrow integration this patch adds

1. cgx/domain_templates/achilles_owner_operator_profile.json — typed, review-only P.A intent, operator role, existing components, source ladder, first UniSpace delivery task, permission ceiling and holds.
2. plugins/packages/achilles/references/selector.json — generated plugin selector intentionally remains unchanged; the separate owner-profile is loaded by the review packet script. Existing emassc default is preserved.
3. scripts/prepare_achilles_owner_packet.py — deterministic non-dispatching owner packet, optionally using existing cognigrex_supervisor.build_workflow_plan; SHA-256 hashes private identifiers without including their raw contents.
4. tests/test_achilles_owner_packet.py — negative tests for privilege escalation, foreign domain, unsafe floor routing, duplicate references, source leakage and CLI private-file usage.

Example read-only packet preparation: provide a controlled local instruction file rather than a shell argument.

    python scripts/prepare_achilles_owner_packet.py --instruction-file /private/owner-task.txt --task-id ACHILLES-UNISPACE-DELIVERY-REVIEW-001 --project-id UniSpace --output /private/review/achilles-owner-packet.json

This packet does not itself execute models, queue tasks, mint Object_IDs, approve permissions or install code.

## First host task after independent gates

1. Reconcile Task_ID with existing GO queue and last receipt before any dispatch (no duplicate).
2. Verify registered host, exact source, live lease/issuer/revocation, ACL and owner authority.
3. Route via existing run_cgx_agent_runtime.py using --agent-id Achilles --domain emassc, without bypassing tool gates.
4. Neo/LightSpeed produces the minimum-sufficient specialist result, with hash-bound evidence.
5. Achilles returns the owner decision packet; independent authority and DBR readback precede any effectful action.
6. UniSpace displays only ACL-qualified R3 information; autonomy growth follows proposal -> isolated tests -> independent review -> signed promotion.

Open stop ships: #154, #158, #161, #209, S92/S97. No PR auto-merge, credential installation, public publication or scheduled agent wake-up follows from this patch.

## 1 November: LS GO singleton consumer health integration (review stage)

The owner-local source review confirmed that an HTTP-responsive LS GO bridge does **not**
prove the singleton Smith/Neo consumer is healthy. In the observed Windows host
state, the consumer heartbeat was stale and its recorded process ID had been
reused by an unrelated process. The existing native queue and database identities
were read-only and not modified.

The additive `scripts/achilles_lsgo_consumer_preflight.py` uses a bounded Windows
process query and existing lock metadata to classify stale heartbeats, reused PIDs,
wrong processes and malformed locks. It **never** deletes a lock, restarts a service,
authenticates the owner, obtains leases, submits a queue item, or grants execution.
Even a fresh matching Python process is only a candidate until authenticated
thread, lease, owner and receipt proof independently pass.

`tests/test_achilles_lsgo_consumer_preflight.py` provides fail-closed test coverage.
The exact source/test Git blobs were run in a private BouwerBase review staging
environment, where eight built-in negative checks and thirteen focused pytest
cases passed; this is not a Stage35 host acceptance or native installation.

The host-local queue review adapter separately verified exact-command-ID lookup,
duplicate/DB identity alignment and source-reference-only search. Its initial
non-dispatching UniSpace task packet remains owner-private, never a new source of
truth or separate scheduler. The existing LS GO command ledger and consumer
retain ownership. Do **not** queue tasks while singleton consumer readiness is
unverified; require exact owner-authorised recovery of the original service,
durable task/claim receipt reconciliation, and an independent post-restart
heartbeat/consumer readback.

The unminted Achilles profile, generated plugin selector and existing approval
and Stage35 pins remain unchanged.
