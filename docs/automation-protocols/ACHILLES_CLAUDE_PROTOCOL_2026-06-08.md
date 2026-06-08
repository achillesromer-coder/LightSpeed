# Achilles / Claude Execution Protocol — 2026-06-08

Canonical `.Claude` file: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\.claude\ACHILLES_CLAUDE_PROTOCOL_2026-06-08.md`

Result label: `ACHILLES_CLAUDE_PROTOCOL_REPO_MIRROR_READY`

Use the `.Claude` file as the executable operator protocol. This repo mirror exists so GitHub, Desktop Codex, Terminal Codex, Co-Runner, and build reviewers can inspect the same operating frame.

## Run order

1. Recheck GitHub, Google Drive, and Gmail connector profile status.
2. If authenticated, use live Drive docs/Sheets first; if not, record `[x] missing value: connector authenticated profile` and proceed from local/repo handoff records.
3. Use only concrete values, bounded ranges, or `[x] missing value: ...` entries.
4. Run local validations before any commit/push.
5. Do not merge `Main`, mutate Drive, send Gmail, publish routes, deploy production, or touch secrets without explicit operator approval and a verified tool channel.

## Staggered automation rotation

| Minute | Automation | Primary files |
|---:|---|---|
| `:00` | Achilles source-of-truth sweep | Registers, CL gate, commit state |
| `:12` | Drive and Co-Runner review sweep | Drive docs, review queue, Co-Runner docs |
| `:24` | Desktop/Terminal Codex execution audit | Local shell, Git, route checks |
| `:36` | Claude/UI artifact and agent-lane build pass | `.Claude`, UI artifact, per-agent oversight docs |
| `:48` | Launch gate and maintenance handoff compact | Compact handoff, blockers, next-hour queue |

## Agent oversight package

- Canonical index: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs\agent-oversight\00_AGENT_OVERSIGHT_INDEX_2026-06-08.md`
- Review mirror: `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review\agent_oversight`

## Required output schema

- `run_label`
- `tool_state`
- `source_records_used`
- `actions_completed`
- `missing_values`
- `blocked_actions`
- `next_handoff`
