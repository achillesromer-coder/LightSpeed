# LS GO Sites side-edit integration — 2026-07-20

## Target

The existing LightSpeed GO Site remains the only Site target:

`https://lightspeed-go.nathaniel-b.chatgpt.site/`

This pass does not create a replacement Site, duplicate command centre, parallel deployment, or alternate public surface.

## Current source stack

- Git implementation: `apps/lightspeed-go` on `achillesromer-coder/LightSpeed`.
- Drive shell/control plane: `LightSpeed_Web_Shell_Builder_CL3_v0_2`.
- Drive execution register: `LS_GO_Queue_2026_07_07`.
- Desktop execution bridge: `tools\run_ls_go_bridge.cmd` and the local LS GO bridge runtime.
- Site publication: the current ChatGPT Sites edit context for the existing Site.

## Side-edit rule

Preserve the current four-view application:

1. Command
2. Activity
3. System
4. Sources

The side-edit layer is additive. It mounts after the existing application and adds only:

- current-Site identity;
- Nathaniel Bower owner orientation;
- Achilles / GO control-gate chain;
- Git and Drive source-parity status;
- review/publish state.

The side-edit module is isolated in `src/siteSideEdit.ts`, loaded after `src/main.ts`. Removing that one script reference reverts the augmentation without reconstructing the application.

## Consolidation decisions

Older Drive builder modules were reviewed rather than copied wholesale.

- Duplicate application authentication is not promoted. ChatGPT Sites audience and access controls remain the Site access boundary.
- Private user-profile and Google-account data remain outside the published Site.
- Older broad route-shell dashboards are not restored into the simplified command centre.
- Desktop commands remain local, bounded, reviewable and receipt-backed.
- Drive remains the evidence/workbook control layer; Git remains implementation authority.

## Sites edit instruction

Open the existing Site from the Sites sidebar or the chat where it was created, choose Edit, and apply the current `apps/lightspeed-go` source as a delta to the referenced Site. Do not create a new Site. Review the private preview first, then publish the updated version to the existing Site URL.

## Acceptance checks

- Existing Site is referenced before editing.
- No new Site or new slug is created.
- Command, Activity, System and Sources remain intact.
- Owner/GO hierarchy and source parity are visible.
- No private Drive payload or secret is included.
- `npm test`, `npm run check` and `npm run build` pass.
- The existing Site URL is verified after publish.
- Git, Drive and Sites receipts record the same release state.
