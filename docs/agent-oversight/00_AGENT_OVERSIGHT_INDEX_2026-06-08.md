# Agent Oversight Index — 2026-06-08

Result label: `AGENT_OVERSIGHT_ARTIFACTS_CREATED__MAINTENANCE_BACKEND_READY`

## Purpose

This index binds the Achilles console concept to concrete per-agent oversight artifacts. Each artifact is a backend maintenance/control record: it identifies source authority, tool dependencies, execution boundaries, output schema, missing values, and the next handoff for its lane.

## Active oversight artifacts

| Lane | Artifact | Recurring task minute | Current state |
|---|---|---:|---|
| Achilles Core | `ACHILLES_CORE_OVERSIGHT_2026-06-08.md` | `:00`, `:48` | Governance/source-of-truth control active from local/repo records |
| Co-Runner | `CO_RUNNER_OVERSIGHT_2026-06-08.md` | `:12` | Drive-backed review lane blocked on connector re-auth |
| Desktop Codex | `DESKTOP_CODEX_OVERSIGHT_2026-06-08.md` | `:24` | Local execution and repo branch audit active |
| Terminal Codex | `TERMINAL_CODEX_OVERSIGHT_2026-06-08.md` | `:24` | Shell validation lane active, destructive commands blocked |
| Claude/UI | `CLAUDE_UI_OVERSIGHT_2026-06-08.md` | `:36` | `.Claude` protocol and UI/control artifact lane active |
| Local Runners | `LOCAL_RUNNER_OVERSIGHT_2026-06-08.md` | `:48` | Ollama/local runner bridge remains dry-run and one-session gated |

## Shared source paths

- Protocol: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\.claude\ACHILLES_CLAUDE_PROTOCOL_2026-06-08.md`
- Recurring tasks: `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\docs\automation-protocols\ACHILLES_RECURRING_TASK_REGISTER_2026-06-08.md`
- Review mirror: `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review\agent_oversight`
- LightSpeed branch: `cl3/ls-go-launch-alignment-2026-06-07`
- Latest pushed protocol commit: `00590d0`

## Current missing values

- `[x] missing value: GitHub connector authenticated profile`; observed value: `token_expired` 401.
- `[x] missing value: Google Drive connector authenticated profile`; observed value: `token_expired` 401.
- `[x] missing value: Gmail connector authenticated profile`; observed value: `token_expired` 401.
- `[x] missing value: /ls-go/agents public route HTTP 200`; observed value: `ERROR: HTTP Error 404: Not Found`.

## Completion condition

These artifacts remain build-oversight records until connector auth, Drive source reads, route gates, reviewed PR/merge path, and per-agent maintenance handoffs are all complete. After that, they become backend cross-platform maintenance records.
