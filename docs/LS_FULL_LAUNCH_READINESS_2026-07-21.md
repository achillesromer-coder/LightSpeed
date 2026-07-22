# LightSpeed full-launch readiness — refreshed 2026-07-22

Status: `OPERATIONAL_PRIVATE / RESOURCE_GUARDED / FULL_LAUNCH_HELD_FOR_OWNER_REVIEW`

## Accepted baseline

- Repository: `achillesromer-coder/LightSpeed`.
- Current main commit: `33b5e626b7301a86335736535af238d7de8dcd02`.
- Accepted integration sequence:
  - PR #15 — complete private soft-launch integration;
  - PR #17 — Merovingian liveness and canonical C/D storage authority;
  - PR #18 — all-floor asynchronous health and independent C:/D: guards;
  - PR #19 — physical-memory pressure guard and bounded-operation policy.
- Existing LS GO Site: `https://lightspeed-go.nathaniel-b.chatgpt.site`.
- Site version: `8`.
- Site access: `private_owner_only`.
- Recorded Site source commit: `10d33303eeed385cd6f3c21a3b1367873f97beb2`.
- Deployment receipt: `lightspeed_go_site_deployment_receipt_2026-07-21.json` in the existing Drive Project Receipts folder.
- Drive Project Receipts folder: `1FlIjBrt3vQG67Jh37aWGf2cVEa6OmXZX`.

The existing Site was updated in place. No replacement Site was created.

## Current operational evidence

- Full local stack receipt: pass at the accepted soft-launch checkpoint.
- De Sporte probe and Desktop population receipts: pass; canonical root `D:\De Sporte`; populated `de_sporte_runtime` summary recorded.
- Merovingian database, event bus and storage: pass at the persisted health receipt; 33 database tables recorded.
- Project artifact chain: one immutable RFS/EMFF README copy, byte size and SHA-256 manifest, GO approval and decision receipt are present in Drive.
- PR #17 live checkpoint: supervisor PID alive, heartbeat fresh, 8 active projects, 0 empty projects and 0 cleanup candidates.
- PR #18 checkpoint: all 8 floors operational; shared Neo, review and decision transports present; D: had about 100.8 GiB free and 54.58% used.
- PR #19 checkpoint: memory pressure is incorporated into the same resource guard. The accepted host observation was roughly 10% free memory, so new heavy work is bounded/held while existing services and review queues remain available.
- PR #19 CI: LightSpeed Surface Validation and Merovingian Project Routing passed.
- Source manifest: 613 eligible records validated; 83 Raphael/N3-adjacent records excluded by package boundary.
- Existing private Site v8 remains the accepted front-facing rollback surface.

## Full-launch gates

A full launch is ready for owner decision only when every required gate below is current at the release checkpoint.

### FL-01 — owner release decision

Required state: `APPROVED`.

Nathaniel remains final authority. Achilles/GO records the decision. Neo routes only after the decision exists. This document does not grant approval.

### FL-02 — publication target and visibility

Required state: exact target recorded.

The owner must choose the intended visibility state for the existing Site. Current state is `private_owner_only`. Public or wider access must not be inferred from the private deployment receipt.

### FL-03 — current source and Site parity

Required state: `PASS_AT_RELEASE_CHECKPOINT`.

Record:

- current LightSpeed main commit;
- Site source commit;
- Site version and deployment ID;
- exact route and access state;
- build, lint and test receipt;
- live read-back timestamp;
- confirmation that runtime-only changes are either represented on the Site or intentionally outside the Site bundle.

The current main commit is newer than the recorded Site source commit. Until the exact current source/Site relationship is rechecked, this gate is held rather than inferred.

### FL-04 — pre-release health and resource checkpoint

Required state: `PASS_OR_ACCEPTED_BOUNDED_WARNING` immediately before release.

Verify:

- Desktop API online;
- Merovingian supervisor process alive and heartbeat fresh;
- database, event bus and storage healthy;
- LS GO bridge healthy;
- all expected floors and project inventory readable;
- no failed actionable queue item;
- C: and D: storage above critical thresholds;
- free memory above the critical threshold;
- heavy work held whenever memory or disk state is warning/critical;
- no unexpected outbound data destination;
- approved review records remain readable;
- Drive receipt path is writable or an explicitly accepted bounded outbox is active.

Resource policy:

- disk warning at 75% used;
- disk critical at 90% used or under 25 GiB free;
- memory warning under 15% free;
- memory critical under 8% free or under 2 GiB free;
- critical pressure holds heavy work without terminating user applications.

### FL-05 — command and artifact receipt

Required state: one current bounded end-to-end receipt.

Use the owner/Achilles GO gate, Neo routing and a permitted local execution floor. Record command envelope, result, immutable artifact manifest where files are involved, evidence and final decision. Do not expose local Desktop execution publicly.

The historical RFS/EMFF receipt proves the mechanism. A release checkpoint requires a current receipt or an explicit owner waiver tied to the unchanged command path.

### FL-06 — privacy, package, claim and secret boundaries

Required state: `PASS`.

- No private Drive payload on the Site.
- No raw API keys, credentials, wallet, payment, custody or token material in Git, Drive receipts, Slack or Site state.
- Provider credentials are environment-only and redacted from generic settings exports.
- No public Desktop execution.
- No scientific claim promotion from uninstrumented or screening results.
- Raphael, N3/GeoMatrices, EML#F and independent protected packages remain outside the LightSpeed launch payload except for explicit read-only provenance references.
- De Sporte remains read-only unless separately approved.

PR #20 is the current provider-secret hardening review. External OpenAI/Anthropic provider activation remains held until that boundary passes and a local owner-controlled environment receipt exists. Local Ollama operation may continue independently.

### FL-07 — rollback readiness

Required state: `READY`.

Current and rollback anchors:

- current Git main: `33b5e626b7301a86335736535af238d7de8dcd02`;
- accepted private soft-launch base: `5e73543778978ec0c269293808df7badce213a36`;
- liveness/storage checkpoint: `238c2c830cdf1c096e00612ed616ca2a21da34b9`;
- all-floor/storage checkpoint: `cac4e9f27e686b1eebd065544b26d35010c6a7b9`;
- Site: accepted private version `8`;
- Drive: accepted deployment, local-stack, De Sporte, Merovingian and artifact-review receipts in the existing Project Receipts folder.

Hold or rollback when health fails, resource state reaches critical, source/Site parity breaks, an unauthorised queue item appears, privacy boundaries fail or the owner decision is absent.

### FL-08 — monitoring and incident routing

Required state: `ACTIVE`.

- Achilles: governance and owner-decision gate.
- Neo: cross-surface routing and return packets.
- Architect: canonical project/dependency/release packet.
- TheConstruct: bounded simulation only; heavy work manual and resource-gated.
- Morpheus: corroboration and promotion review.
- Oracle: provenance, knowns and source intake.
- Smith: build, test, queue and execution receipts.
- Merovingian: liveness, memory, storage, project, artifact and recovery evidence.
- Trinity: operator and Site surface verification.

Notify only on meaningful change, failure, mismatch, owner decision, deployment or rollback condition.

### FL-09 — provider integration boundary

Required state: `EXTERNAL_PROVIDER_DISABLED` or `SECURE_PROVIDER_GATE_PASSED`.

- OpenAI key creation uses the secure Platform setup flow.
- The raw key must be installed only as `OPENAI_API_KEY` in the owner-controlled local environment or approved secret manager.
- The key must not be pasted into Desktop settings, Git, Drive, Slack or a Site.
- Provider activation requires PR #20 CI pass, owner approval and one redacted local adapter receipt.
- Provider activation is not required for the existing local Ollama-based private soft launch.

## Known held items

- Current source/Site parity must be rechecked against main `33b5e626...` before visibility expansion.
- The accepted host memory observation was in warning territory; heavy work remains bounded until memory recovers.
- The Windows visual-capture interface previously returned `0x80004002`; this remains a capture-tool limitation, not visual proof.
- External provider activation remains held pending PR #20 and owner-controlled environment configuration.
- Public/wider Site access is not recorded as approved.
- Scientific and regulatory claims remain governed independently of software launch readiness.

## Launch sequence after explicit owner approval

1. Re-run FL-03 through FL-06 and FL-09 against current main.
2. Confirm resource state is pass or an explicitly accepted bounded warning; do not release under critical pressure.
3. Apply the approved visibility change to the existing Site only.
4. Verify the exact route, source parity and access state.
5. Run one bounded end-to-end command and retain its receipt.
6. Write the release receipt to Drive, LS GO Queue and CORE.
7. Continue liveness, memory, storage and queue reconciliation.
8. Hold or rollback immediately on a failed gate.

## Current disposition

`READY_FOR_OWNER_REVIEW_WITH_RESOURCE_AND_PROVIDER_GATES`.

No full/public launch, visibility expansion, external-provider activation, deletion or protected-package expansion is performed by this readiness packet.
