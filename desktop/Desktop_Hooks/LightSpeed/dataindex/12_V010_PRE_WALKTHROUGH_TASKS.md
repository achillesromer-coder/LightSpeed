# V0.10.0 Pre-Walkthrough Task Board

This board is the current gating list before the first full desktop walkthrough, approval pass, debug sweep, and D-root publish snapshot.

## Current 9am Walkthrough Status

- Bridge health tile implemented: `Z Axis/Z+3_Trinity/data/ui/bridge_health.json`
- 9am runbook/readiness contract implemented: `Z Axis/Z+1_Architect/data/finalization/walkthrough_readiness.json`
- Current bridge state: `ready_with_warnings`, `87.5%` readiness.
- Current walkthrough state: `walkthrough_ready_with_warnings`, `0` blocked, `3` warnings, `1` publish hold.
- Public route contract is present for `/`, `/operations`, `/operations/w1` through `/operations/w6`, `/gmat`, `/library`, `/docs`, and `/dash`.
- Live route probe: `12/12` public routes returned HTTP `200`; `/data/*` and `/w*/data` returned HTTP `401` and should be treated as auth-gated dataspaces until payload access is configured.
- Known warnings: data endpoints need authenticated JSON/table payloads or explicit maintenance stubs; second Drive folder and desktop population Sheet need sharing or local-table gating.
- Current proof baseline: `tests/test_runtime_package.py` is `85/85`; contract/path/oracle/runtime package suite is `106/106`.
- D-root publishing remains blocked until after human walkthrough approval.

## A. Website, Drive, and Sheets Bridge

1. Confirm `/operations`, `/operations/w1` through `/operations/w6`, `/gmat`, `/library`, `/docs`, and `/dash` remain public `200` routes before walkthrough.
2. Confirm `/data/achilles`, `/data/directory`, and `/w1/data` through `/w6/data` either return authenticated JSON/table payloads or explicit maintenance status.
3. Fix public spelling/label issues before release notes are cut.
4. Share the second Drive folder with the connector account or mark it disabled in Trinity settings.
5. Share the desktop population Sheet with the connector account or keep the app in local-table-only mode.
6. Map `Website Logs` tabs to Oracle datatables, Smith handoff queues, and Architect publish flags.
7. Keep public `/operations/w6` as a compatibility facade while removing W6 as an internal filing system.
8. Add a bridge-health tile to the bento dashboard showing website, Drive, Sheets, and dataspace status.
9. Ensure Neo/Achilles writes require approval when `achilles_write_enabled` is `conditional`.
10. Keep `publish_flag` as the external-reporting gate for website-facing rows.

## B. Desktop Walkthrough Flow

11. Start app, show loading bars, and land on the Smart Bento Project Wall.
12. Create/select a project, enter subfolders/component sets, and verify bento widgets resize/refit.
13. Attach an original file through Oracle and preserve it as the editable source.
14. Run ingestion to extract definitions, object fragments, tasks, strings, and datatable rows.
15. Proof extracted content through Morpheus with confidence/source/publish fields visible.
16. Route approved fragments through Smith/Z Direct with received, updated, completed, deleted, and declassified states.
17. Merge partial object data when later sources fill missing fields.
18. Open TheConstruct map/simulation tiles only after the user enters Holospace or a simulation component.
19. Save simulation/GMAT outputs as revisable ephemeris artifacts.
20. Publish approved artifacts through Architect into the canonical snapshot tree only.

## C. Cleanup, Performance, and Packaging

21. Remove safe generated caches and keep one weekly/table-style log trail instead of one-off note files.
22. Archive stale dataindex notes into Merovingian reports after their contents are represented in contracts or code.
23. Verify startup wizard, guided settings wizard, floor/widget settings, and `Ctrl+Shift+S` all call the same Trinity settings library.
24. Verify `Ctrl+S` search, `Ctrl+Shift+S` settings, `Ctrl+K` command palette, right-click context menus, and Holospace-only WASD behavior.
25. Verify missing dependencies create Neo approval tasks and empty landing tables rather than crashing.
26. Run `python -m pytest tests/test_config_contracts.py tests/test_path_ownership_contracts.py tests/test_oracle_data_contracts.py tests/test_runtime_package.py -q`.
27. Run `python N.py --smoke`.
28. Run `python __main__.py --verify`.
29. Run a route/Drive bridge validation pass and update `romer_web_integration.json`.
30. After human walkthrough approval, overwrite the D-root snapshot and mark the package `V0.10.0`.
