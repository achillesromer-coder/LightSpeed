# Web 2.0 Hybrid Prepublish Review v0.1

Status: **IN-CHAT REVIEW ACTIVE / NOT PUBLICLY RELEASED**

## Purpose

Provide one bounded review bridge between Drive canon, ChatGPT in-chat visualization, GitHub implementation staging and the later public Web 2.0 surface.

This layer is deliberately **pre-implementation**. It allows the owner and reviewers to inspect the exact public-safe candidate, evidence labels, exclusions and publication gates before the formal prepublish review and before any primary web release.

## Authority model

1. **Google Drive** — canonical content/evidence/control authority. Current controlling surfaces include `68_Web_Copy_Blocks_v0_6`, `97_PUBLICATION_GATE_v1_1`, `154_INTERSOL_MASTER_READOUT_v0_1`, `157_INTERSOL_EXPORT_MANIFEST_v0_1`, and `159_INTERSOL_PUBLISH_HANDOFF_v0_1`.
2. **ChatGPT / Visualize** — bounded in-chat review surface. Review decisions made here are not canon until written back to Drive/Git receipts.
3. **GitHub** — review/implementation mirror. This branch contains the machine-readable contract; it is not publication authority and must not be merged solely to satisfy publication timing.
4. **Web implementation** — follows accepted review state through a normal branch/PR route. Public status requires provider deployment/readback evidence.

## Review sequence

`Drive canon → in-chat mini prepublish → formal prepublish review → primary publish review → web implementation → public release receipt`

The in-chat surface may mark copy blocks `APPROVE`, `REVISE`, `HOLD` or `EXCLUDE` and attach local review notes. A formal state change must then be persisted to the canonical Drive surfaces and, where relevant, the Git review contract.

## Current candidate

The current frozen public-safe candidate is `COPY-008` through `COPY-013` from `68_Web_Copy_Blocks_v0_6`:

- `COPY-008` — About Römer Industries
- `COPY-009` — Evidence Before Promotion
- `COPY-010` — A Portfolio Built in Stages
- `COPY-011` — M1 / SEQLD Living Infrastructure Study
- `COPY-012` — InterSol Platform
- `COPY-013` — Watch Tower Digital Reference

`COPY-005` and other restricted/internal-first material remain outside the first-public candidate.

## Gate model

`GATE-012` is satisfied by founder authority. `GATE-001..011`, `GATE-013` and `GATE-014` remain independent claim/content controls.

The review UI must therefore keep visible distinctions between:

- source-backed digital/reference geometry and certified physical engineering;
- tested software and externally validated physical capability;
- conceptual/proposed infrastructure and approved/procured public works;
- bounded operating descriptions and unverified corporate/legal relationships;
- public programme summaries and restricted/security-sensitive detail;
- conceptual economic/token architecture and any regulated or activated financial state.

## Web implementation contract

The accepted candidate should be implemented under `apps/lightspeed-go` or a successor approved web surface only after review. The production implementation must:

- consume JSON/adapters rather than brittle hard-coded Sheets ranges;
- retain stable content IDs and evidence/gate metadata;
- render visible guardrail/evidence states where a claim is bounded;
- keep restricted data out of public payloads;
- use branch/PR review rather than direct `main` mutation;
- avoid live URL/alias changes until the final route/alias audit;
- record exact artifact, target/action and provider readback before asserting `PUBLICLY RELEASED`.

## Current Git state

Review branch: `review/web2-prepublish-hybrid-2026-08-31`

Machine-readable contract: `data/governance/web2_prepublish_review_v0_1.json`

No production route, live alias, deployment or main-branch publication mutation is authorised by this document.
