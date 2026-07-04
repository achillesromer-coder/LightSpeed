# Achilles / Claude Execution Protocol — 2026-06-08

Result label: `ACHILLES_CLAUDE_PROTOCOL_READY__HOURLY_ROTATION_PREPARED`

## Purpose

This `.Claude` protocol gives Claude/UI operators the same execution posture as Achilles, Desktop Codex, Terminal Codex, and Co-Runner: prove current state first, use live tools when authenticated, avoid guessed values, and hand off every blocked value as `[x] missing value: ...` with the observed blocker.

## Current verified tool state

| Tool lane | Observed value | Required handling |
|---|---|---|
| GitHub connector | `[x] missing value: authenticated profile`; observed value `token_expired` 401 | Re-auth before connector PR creation or remote metadata reads |
| Google Drive connector | `[x] missing value: authenticated profile`; observed value `token_expired` 401 | Re-auth before Drive search, doc read/write, Sheet range reads, or writeback |
| Gmail connector | `[x] missing value: authenticated profile`; observed value `token_expired` 401 | Re-auth before digest email read/send/draft |
| Local Git shell | `available`; LightSpeed branch `cl3/ls-go-launch-alignment-2026-06-07` pushed at commit `fdaeabc` | Use for local validation and feature-branch commits only |
| Achilles static gate | `STATIC_GATE_PASS`; local commit `6072580` | Use for no-key automation safety validation |
| Romer routes | `/ls-go`, `/ls-go/status`, `/ls-go/handoff`, `/ls-go/review` observed HTTP `200`; `/ls-go/agents` observed HTTP `404` | Do not call `/ls-go/agents` complete until HTTP `200` is observed |

## Operating rules

1. Start every run by checking connector profile status for GitHub, Google Drive, and Gmail when those tools are callable.
2. If a connector is expired or unavailable, continue with local files and record `[x] missing value: connector authenticated profile`; do not infer Drive, Gmail, or connector-side GitHub state.
3. Use the newest source records first: live Drive docs if authenticated; otherwise local handoff registers under `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review` and repo docs under `docs/`.
4. Never use unresolved filler text. Every field must be either a concrete value, a bounded range, or `[x] missing value: exact missing field`; include the observed blocker.
5. Do not read, print, store, or summarize secret values. Treat OAuth files, `.env`, API credentials, private keys, wallet/token/payment/custody/IPFS data as hard stops.
6. Do not delete, overwrite, merge `Main`, mutate Drive, publish live routes, send Gmail, or deploy production unless the active run has explicit operator approval and a verified tool channel.
7. Keep Achilles as governance/source-of-truth oversight. Co-Runner, Desktop Codex, Terminal Codex, Claude/UI, and local runners execute only their bounded lane and then hand off evidence.

## Source hierarchy

| Priority | Source | Use |
|---:|---|---|
| 1 | Authenticated Google Drive docs and Sheets | Current governance, registers, review queue, agent oversight docs |
| 2 | `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review` | Local review queue, compact handoffs, connector packets |
| 3 | `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs` | Repo-mirrored launch/build records |
| 4 | `C:\Users\acc\Documents\Codex\2026-06-02\files-mentioned-by-the-user-temporary\achilles-drive-ops` | Achilles/Athene static automation gate |
| 5 | Older or backup records | Directional context only; never supersede current registers without evidence |

## Agent oversight package

Use `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs\agent-oversight\00_AGENT_OVERSIGHT_INDEX_2026-06-08.md` as the canonical per-agent oversight index. The review mirror is `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review\agent_oversight`.

## Claude/UI responsibilities

- Present an operator-facing console state without overstating execution authority.
- Surface lanes for Achilles Core, Co-Runner, Desktop Codex, Terminal Codex, Claude/UI, and local runners.
- Summarize current source-of-truth, review queue, route gates, commit state, and missing values.
- Draft handoff/register updates only after verifying source state or marking missing values explicitly.
- Maintain `.Claude` artifacts as UI/agent protocol records, not as secret stores or execution credentials.

## Five-task hourly rotation

Each task runs once per hour, staggered every 12 minutes, so one oversight lane wakes every 12 minutes.

| Minute | Task | Lane | Output expectation |
|---:|---|---|---|
| `:00` | Achilles source-of-truth sweep | Governance/registers | Current register/gate digest with values or `[x] missing value` entries |
| `:12` | Drive and Co-Runner review sweep | Drive/review queue | Review queue delta, Co-Runner doc status, Drive auth state |
| `:24` | Desktop/Terminal Codex execution audit | Local/repo/shell | Git status, route state, local validation commands, blocked execution report |
| `:36` | Claude/UI artifact and agent-lane build pass | Claude/UI/agent artifacts | Per-agent oversight artifact update plan, UI console gaps, prompt/build packet |
| `:48` | Launch gate and maintenance handoff compact | Achilles final gate | Compact handoff, go/no-go blockers, next-hour action queue |

## Per-run output format

Every automation must return:

- `run_label`: exact task label and timestamp.
- `tool_state`: GitHub, Drive, Gmail, local shell, route state.
- `source_records_used`: concrete file/doc names or `[x] missing value: source record access`.
- `actions_completed`: concrete changes or validations completed.
- `missing_values`: each unavailable value in `[x] missing value: ...`; observed value format.
- `blocked_actions`: blocked actions with reason and required unblock.
- `next_handoff`: the next lane and exact file/register to update.

## Required first prompt for Claude/UI

Use this when a Claude/UI operator or artifact begins a run:

```text
You are Claude/UI for Achilles / CCC / LightSpeed CL3. Follow `.claude/ACHILLES_CLAUDE_PROTOCOL_2026-06-08.md`. Check connector/tool state first. Use live Drive only if authenticated; otherwise use local Achilles review queue and repo docs. Never use unresolved filler text. Every absent value must be `[x] missing value: <field>` with the observed blocker. Do not read or print secrets. Do not delete, publish, send Gmail, merge Main, mutate Drive, or deploy production unless explicitly authorized and the tool channel is verified. Return tool_state, source_records_used, actions_completed, missing_values, blocked_actions, and next_handoff.
```

## Completion threshold

The hourly rotation continues until all of the following are true:

- GitHub, Drive, and Gmail connectors report authenticated profiles.
- Required Drive source registers and Sheets are readable.
- `/ls-go/agents` returns HTTP `200` or is explicitly removed from the active launch surface.
- Per-agent oversight artifacts exist for Achilles, Co-Runner, Desktop Codex, Terminal Codex, Claude/UI, and local runners.
- LightSpeed branch has a reviewed PR or an approved merge path.
- Achilles static gate passes and any credentialed automation is behind approved secret handling.
- Maintenance artifacts are converted from build oversight into backend cross-platform maintenance records.
