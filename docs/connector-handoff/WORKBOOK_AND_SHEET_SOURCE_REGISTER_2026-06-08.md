# Workbook And Sheet Source Register — 2026-06-08

Result label: `WORKBOOK_SHEET_SOURCES_INDEXED__CONNECTOR_AUTH_MISSING_VALUES_EXPLICIT`

## Connector workbook authority

- Google Sheet URL: `https://docs.google.com/spreadsheets/d/1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw/edit?usp=sharing`
- Google Sheet ID: `1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw`
- Google Drive connector profile: `[x] missing value: authenticated profile`; observed value: `token_expired` 401.
- Google Sheet metadata/ranges: `[x] missing value: readable workbook metadata and cell ranges`; observed value: `token_expired` 401.
- Action taken: no Drive write, no Sheet edit, no guessed ranges.

## Local workbook and CSV inventory

- Search roots: `D:\LightSpeed_Consolidated`, `D:\To be assimilated`, `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary`.
- Relevant local sheet-like files found excluding `venv`, `node_modules`, and `.git`: 107.

| Path | Bytes | Last write |
|---|---:|---|
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\ls-go-launch-2026-06-07\ls_go_route_observed_check.csv` | 1476 | 2026-06-08 09:22:02 |
| `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs\ls-go-launch\ls_go_route_observed_check.csv` | 1476 | 2026-06-08 09:22:02 |
| `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs\romer-web-hooks\romer_route_header_embed_map.csv` | 6441 | 2026-06-07 11:29:57 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\romer-industries-web-hooks-2026-06-07\romer_route_header_embed_map.csv` | 6441 | 2026-06-07 11:29:57 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\registries\sub_collectives.csv` | 420 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\registries\projects.csv` | 500 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\registries\members.csv` | 608 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\registries\mint_queue.csv` | 372 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\registries\assets.csv` | 784 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\registries\collectives.csv` | 694 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\royalties.csv` | 563 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\sub_collectives.csv` | 420 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\permissions.csv` | 671 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\projects.csv` | 534 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\members.csv` | 606 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\mint_queue.csv` | 357 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\folder_index.csv` | 977 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\glossary.csv` | 711 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\contracts.csv` | 794 | 2026-06-02 10:58:54 |
| `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\platform-ccc\Platform.CCC_upload_root\registries\contributions.csv` | 251 | 2026-06-02 10:58:54 |

## Execution rule applied

- Every unavailable workbook value is recorded as `[x] missing value: ...` with the observed blocker value.
- Local CSV/workbook files are indexed only; no wallet/token/mint/payment/custody/IPFS workflows are activated.
