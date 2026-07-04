# Codex Web/Desktop Launch Pass - 2026-06-16 AEST

Result label: `CODEX_WEB_DESKTOP_LAUNCH_PASS__C_DRIVE_BUILD_GREEN__LIGHTSPEED_AND_DESPORTE_RUNNING__PUBLISH_GATE_BLOCKED_BY_AUDIT`

## Source Records

- `C:\Cognigrex\00_COGNIGREX_LAUNCH_MAP_2026-06-16.md`
- `C:\Cognigrex\00_COGNIGREX_LAUNCH_MAP_2026-06-16.json`
- `D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\verify_launch_ready.py`
- `D:\LightSpeed_Consolidated\LightSpeed_Runtime\tests`
- `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\apps\lightspeed-go`
- `C:\Cognigrex\WebSurfaces\lightspeed-go`

## Completed

- Confirmed active LightSpeed desktop launcher still points to `D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\LAUNCH_GUI.bat`.
- Confirmed active De Sporte launcher still points to `D:\De Sporte`\`.
- Confirmed packaged De Sporte candidate exists at `C:\Cognigrex\DeSporte_Isolated\application\DeSporte-20260616\DeSporte.exe`.
- Staged LS Go app to `C:\Cognigrex\WebSurfaces\lightspeed-go` because D-drive dependency install failed with `ENOSPC`.
- Ran `npm.cmd install` and `npm.cmd run build` successfully from C staging.
- Started LS Go local preview at `http://127.0.0.1:4173/`; HTTP probe returned `200`.
- Created packaged De Sporte desktop shortcut: `C:\Users\acc\Desktop\De Sporte Packaged.lnk`.
- Corrected packaged De Sporte shortcut to pass `--data-root "C:\Cognigrex\DeSporte_Isolated\application\DeSporte-20260616\Data" --play --window-type onscreen`; the no-argument packaged executable exits.
- Verified packaged De Sporte stays resident when launched with the explicit Cognigrex data root.
- Verified LightSpeed desktop launch readiness: `22/22`, `100%`.
- Verified focused runtime tests: `28 passed`.
- Wrote canonical C:\Cognigrex launch map.

## Build Evidence

```text
LS Go C staging:
npm.cmd run build
vite v7.3.5
dist/index.html
dist/assets/index-DGyZNffG.css
dist/assets/index-CU4L4oCF.js
```

## Remaining Gates

- npm audit reports two high-severity advisories through Vite/esbuild. Fix path requires a Vite 8 major upgrade or explicit temporary launch acceptance.
- The D-drive LS Go dependency install remains blocked by low disk space.
- The web source worktree still has uncommitted Claude UI changes; do not push/merge until reviewed.
- Public route publish remains blocked until route authority and audit/dependency decision are confirmed.
- Drive writeback, Gmail send, GitHub PR creation, and production deploy remain approval-gated.

## Cleanup Classification

No empty repository was deleted. The `.git` folders found are review candidates only, because they may contain nested history or tracked state:

- `D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\Z Axis\Z-1_Morpheus\organization\legacy\Z+2_Morpheus\library\Library\web Calculators\Web-Calculators\.git`
- `D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\Z Axis\Z0_TheConstruct\data\reservoirs\Library\web Calculators\Web-Calculators\.git`
- `D:\LightSpeed_Consolidated\_analysis_remote\LightSpeed\.git`

## Next Safe Actions

1. Decide whether to upgrade Vite to clear advisories or hold static shell behind a no-publish gate.
2. Re-run C staging build after dependency decision.
3. Capture active UI proof for LightSpeed and De Sporte.
4. Prepare web publish packet only after audit/build/route gates are green.
