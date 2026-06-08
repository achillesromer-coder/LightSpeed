# Co-Runner Oversight — 2026-06-08

Result label: `CO_RUNNER_OVERSIGHT_READY__DRIVE_REVIEW_LANE_DEFINED`

## Lane role

Co-Runner owns live review cadence once Drive is authenticated: newest Drive changes, review queue deltas, viewed-vs-modified gaps, Co-Runner protocol docs, and handoff drafts. Until Drive is authenticated, it uses local/repo mirrors and records unavailable Drive fields as missing values.

## Source authority

| Source | Current value |
|---|---|
| Google Drive account | `[x] missing value: authenticated profile`; observed value: `token_expired` 401 |
| Drive docs/Sheets | `[x] missing value: readable Drive docs and Sheet ranges`; observed value: `token_expired` 401 |
| Local Drive writeback packet | `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review\DRIVE_WRITEBACK_PACKET_2026-06-08.md` |
| Workbook/source register | `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review\WORKBOOK_AND_SHEET_SOURCE_REGISTER_2026-06-08.md` |

## Required checks

- Re-auth status for Google Drive.
- If authenticated, search/open current Achilles, CCC, ACR, Co-Runner, Desktop Codex, Terminal Codex, and LightSpeed Go docs.
- If authenticated, compare viewed and modified timestamps for review queue flags.
- If not authenticated, record missing document IDs, Sheet ranges, and review queue fields.
- Draft handoff/register updates only; never live-write without an explicit verified approval.

## Output contract

- `run_label`
- `drive_tool_state`
- `drive_records_used`
- `review_queue_delta`
- `corunner_docs`
- `missing_values`
- `next_handoff`

## Hard stops

- No Drive moves, deletes, overwrite writes, sharing changes, or Sheet edits without authenticated connector and explicit approval.
- No assumptions about Drive contents while connector state is `token_expired`.
