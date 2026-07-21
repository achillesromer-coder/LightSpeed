# LightSpeed full-launch readiness — 2026-07-21

Status: `OPERATIONAL_PRIVATE / FULL_LAUNCH_HELD_FOR_OWNER_REVIEW`

## Accepted baseline

- Repository: `achillesromer-coder/LightSpeed`.
- Main commit: `5e73543778978ec0c269293808df7badce213a36`.
- Accepted integration: PR #15, `Complete LightSpeed soft launch integration`.
- Existing LS GO Site: `https://lightspeed-go.nathaniel-b.chatgpt.site`.
- Site version: `8`.
- Site access: `private_owner_only`.
- Site source commit: `10d33303eeed385cd6f3c21a3b1367873f97beb2`.
- Deployment receipt: `lightspeed_go_site_deployment_receipt_2026-07-21.json` in the existing Drive Project Receipts folder.

The existing Site was updated in place. No replacement Site was created.

## Current operational evidence

- Full local stack receipt: pass.
- Desktop API: online.
- Merovingian: healthy.
- De Sporte: present as read-only Desktop project 11.
- Desktop-visible projects: 11.
- Neo exchange records: 2.
- Tabby and Ollama loopback services: online during the accepted receipt.
- Site build: pass.
- Site lint: pass.
- Site tests: 2 passed.
- Live Site read-back: pass.
- PR #15 validation: Python 15 passed; GO 10 passed; TypeScript passed; Vite production build passed; npm audit reported zero vulnerabilities.
- Source manifest: 613 eligible records validated; 83 Raphael/N3-adjacent records excluded by package boundary.

## Full-launch gates

A full launch is ready for owner review when all gates below remain true at the release checkpoint.

### FL-01 — owner release decision

Required state: `APPROVED`.

Nathaniel remains final authority. Achilles/GO records the decision. Neo routes only after the decision exists. This document does not grant approval.

### FL-02 — publication target and visibility

Required state: exact target recorded.

The owner must choose the intended visibility state for the existing Site. Current state is `private_owner_only`. Public or wider access must not be inferred from the private deployment receipt.

### FL-03 — source and Site parity

Required state: `PASS`.

Record:

- LightSpeed main commit;
- Site source commit;
- Site version and deployment ID;
- exact route;
- build, lint and test receipt;
- live read-back timestamp.

Any source/Site mismatch is a hold condition.

### FL-04 — pre-release health checkpoint

Required state: `PASS` immediately before release.

Verify:

- Desktop API online;
- Merovingian healthy;
- LS GO bridge healthy;
- project inventory readable;
- no failed actionable queue item;
- no unexpected outbound data destination;
- approved review records remain readable;
- Drive receipt path is writable or an accepted bounded outbox is active.

### FL-05 — command-path receipt

Required state: one bounded end-to-end receipt.

Use the owner/Achilles GO gate, Neo routing and a permitted local execution floor. Record command envelope, result, evidence and final decision. Do not expose local Desktop execution publicly.

### FL-06 — privacy, package and claim boundaries

Required state: `PASS`.

- No private Drive payload on the Site.
- No secrets, credentials, wallet, payment, custody or token functionality.
- No public Desktop execution.
- No scientific claim promotion from uninstrumented or screening results.
- Raphael, N3/GeoMatrices, EML#F and independent protected packages remain outside the LightSpeed launch payload except for explicit read-only provenance references.
- De Sporte remains read-only unless separately approved.

### FL-07 — rollback readiness

Required state: `READY`.

Rollback anchor:

- Git: main commit `5e73543778978ec0c269293808df7badce213a36`.
- Site: accepted private version `8`.
- Drive: accepted deployment and local-stack receipts in the existing Project Receipts folder.

Hold or rollback when health fails, source/Site parity breaks, an unauthorised queue item appears, privacy boundaries fail or the owner decision is absent.

### FL-08 — monitoring and incident routing

Required state: `ACTIVE`.

- Achilles: governance and owner-decision gate.
- Neo: cross-surface routing and return packets.
- Smith: health, build, test and execution receipts.
- Oracle: independent reasoning and claim-language review where required.
- Morpheus: source and provenance mapping.
- Trinity: Site and operator-surface verification.
- Merovingian: local health, storage and project change receipts.

Notify only on meaningful change, failure, mismatch, owner decision, deployment or rollback condition.

## Known held items

- The Windows visual-capture interface previously returned `0x80004002`; this is a capture-tool limitation and is not treated as runtime failure or visual proof.
- Three empty legacy project directories remain cleanup candidates. No deletion is authorised.
- Public/wider Site access is not yet recorded as approved.
- Scientific and regulatory claims remain governed independently of software launch readiness.

## Launch sequence after explicit owner approval

1. Re-run FL-03 through FL-06 against the accepted baseline.
2. Apply the approved visibility change to the existing Site only.
3. Verify the exact route and access state.
4. Run one bounded end-to-end command and retain its receipt.
5. Write the release receipt to Drive, LS GO Queue and CORE.
6. Continue health and queue reconciliation.
7. Hold or rollback immediately on a failed gate.

## Current disposition

`READY_FOR_OWNER_FULL_LAUNCH_REVIEW`.

No full/public launch, visibility expansion, deletion or protected-package expansion is performed by this readiness packet.
