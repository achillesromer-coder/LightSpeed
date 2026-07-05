# Achilles Recurring Task Register — 2026-06-08

Result label: `ACHILLES_RECURRING_TASKS_CREATED__HOURLY_12_MINUTE_ROTATION`

## Schedule

Five automations are active. Each runs once per hour and the set alternates every 12 minutes.

| Minute | Automation ID | Name | Primary lane |
|---:|---|---|---|
| `:00` | `achilles-source-truth-sweep` | Achilles Source Truth Sweep | Governance/registers |
| `:12` | `achilles-drive-corunner-sweep` | Achilles Drive CoRunner Sweep | Drive/review queue/Co-Runner |
| `:24` | `achilles-codex-execution-audit` | Achilles Codex Execution Audit | Desktop Codex/Terminal Codex/local shell |
| `:36` | `achilles-claude-ui-build-pass` | Achilles Claude UI Build Pass | `.Claude`, UI artifact, per-agent oversight |
| `:48` | `achilles-launch-gate-compact` | Achilles Launch Gate Compact | Launch gate, blocker compact, maintenance handoff |

## Shared execution frame

- Protocol: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\.claude\ACHILLES_CLAUDE_PROTOCOL_2026-06-08.md`
- Repo mirror: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs\automation-protocols\ACHILLES_CLAUDE_PROTOCOL_2026-06-08.md`
- LightSpeed cwd: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07`
- Achilles local gate cwd: `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\achilles-drive-ops`
- Execution environment: `local`
- Model: `gpt-5.2`
- Reasoning effort: `medium`

## Required output schema

Every recurring run must return:

- `run_label`
- `tool_state`
- `source_records_used`
- `actions_completed`
- `missing_values`
- `blocked_actions`
- `next_handoff`

## Current connector values

- GitHub connector: `[x] missing value: authenticated profile`; observed value: `token_expired` 401.
- Google Drive connector: `[x] missing value: authenticated profile`; observed value: `token_expired` 401.
- Gmail connector: `[x] missing value: authenticated profile`; observed value: `token_expired` 401.

## Safety boundary

The recurring tasks may inspect, validate, summarize, draft, and hand off. They must not read or print secrets, delete files, merge `Main`, mutate Drive, send Gmail, publish routes, deploy production, or activate wallet/token/mint/payment/custody/IPFS workflows unless a future run has both a verified tool channel and an explicit operator approval record.
