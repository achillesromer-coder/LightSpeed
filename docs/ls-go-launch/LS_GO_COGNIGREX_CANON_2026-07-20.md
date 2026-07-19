# LightSpeed GO and base cognigrex canon — 20 July 2026

## Canonical state

The current LightSpeed GO implementation is `apps/lightspeed-go` on `achillesromer-coder/LightSpeed`.

The sole publication surface is the existing ChatGPT Site:

`https://lightspeed-go.nathaniel-b.chatgpt.site/`

The accepted implementation chain is:

1. PR #9 — simplified LS GO command centre and bounded Desktop bridge.
2. PR #10 — additive current-Site side edit.
3. Main source commit — `140dd4ad2d173123b95411fa55a9443b5fa785bd`.
4. Drive receipt — `LS_GO_Queue_2026_07_07`, GO-TASK-0003 and GO-TASK-0004 complete.
5. Site receipt — existing Site retained and current integration published.

No replacement Site, alternate slug or parallel command centre is canonical.

## Base cognigrex definition

A cognigrex is the coordinated operating system formed by the owner, governance gate, agents, tools, implementation surfaces, evidence stores and human approvals. It is not a separate autonomous authority.

### Authority and execution chain

| Layer | Canonical role |
|---|---|
| Nathaniel Bower | Owner, final intent and approval authority. |
| Achilles / GO gate | Governance, source truth, safety gates and owner-decision control. |
| Neo | Routing, bounded divvy and handoff packaging. |
| Agent floor | Specialist work under assigned scope and evidence constraints. |
| LightSpeed GO | Operator command, activity, system and source-review surface. |
| LightSpeed Desktop | Local execution, persistence, build proof and receipts. |
| GitHub LightSpeed | Implementation authority and reviewed code history. |
| Drive CORE | Canonical task/index authority and evidence/workbook control layer. |
| ChatGPT Site | Reviewed publication surface only. |

## Product-surface canon

### LightSpeed GO

- Source root: `apps/lightspeed-go`.
- Current views: Command, Activity, System and Sources.
- Browser commands are bounded envelopes requiring Achilles oversight and public-safe/proof-required declarations.
- Desktop execution is local and receipt-backed.
- Browser fallback remains localStorage, copy and download when Desktop is unavailable.

### LightSpeed Desktop

- Canonical operating runtime remains the verified Desktop alignment represented by the merged final-alignment and subsequent LS GO bridge work.
- Desktop is not publicly callable from the Site.
- Heavy Construct work and secondary Z activation remain gated.
- Historical `Desktop_Hooks` and bounded `LightSpeed_Runtime` surfaces remain source/runtime evidence; no deletion or authority inversion is authorised by this canon.

### LightSpeed Web

- The existing GPT-hosted LS GO Site is the current publication surface for the command centre.
- Older Squarespace and broad route-shell materials remain provenance or staged sources, not competing current publication authority.
- No unsupported Vercel, Squarespace or alternate-host deployment is implied.

## Source-of-truth split

| Concern | Authority |
|---|---|
| Tasks, index, extraction state | Drive CORE |
| Code and implementation contracts | GitHub LightSpeed |
| Operator interaction | LightSpeed GO |
| Local execution and receipts | LightSpeed Desktop |
| Public/current Site presentation | Existing ChatGPT Site |
| Historical source extraction | Drive and archived Git provenance until represented in CORE |

GitHub must not become a parallel task authority. Drive must not become an unreviewed executable-code authority. The Site must not expose private Drive payloads, credentials or direct local execution.

## Open-task disposition

### Complete in the current base

- LS GO command-centre simplification.
- Achilles / GO gate and Neo routing representation.
- Loopback-only Desktop command bridge.
- Git and Drive receipt chain.
- Existing-Site additive integration.
- Dedicated LS GO test, type-check and build workflow.
- Current Site identity and source-parity presentation.

### Active but bounded

- CORE extraction of remaining historical LightSpeed tasks and source records.
- Repository-wide maturity controls and branch-protection administration.
- Runtime-authority mapping between historical Desktop source and bounded operator runtime.
- Archive classification and deletion-readiness proof.
- Exact source-parity receipts for future Site revisions.

### Held or excluded

- Workbook mutation from Git automation.
- Replacement Site or duplicate authentication layer.
- Public direct Desktop execution.
- Destructive archive cleanup without extraction and checksum proof.
- Backend launch, payment/custody, wallet/token/mint activation.
- Raphael, N^3, EML#F and secondary Z work unless explicitly reopened.

## Change rule

Future LS GO changes must:

1. start from current `main`;
2. use a bounded branch and pull request;
3. preserve the four current views unless an owner decision explicitly changes them;
4. pass `npm test`, `npm run check` and `npm run build` in `apps/lightspeed-go`;
5. update the public integration manifest and Drive receipt together;
6. edit the existing Site rather than creating a replacement;
7. record publication state only after the exact current Site is verified.

## Stable next release gate

The base cognigrex architecture is complete enough for ordinary bounded LS GO iteration. The next commit opportunity should be opened only for a concrete operator need, defect, source-parity update or reviewed UI improvement. Broad architecture regeneration is not required.
