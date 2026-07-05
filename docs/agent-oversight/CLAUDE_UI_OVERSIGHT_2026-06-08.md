# Claude/UI Oversight — 2026-06-08

Result label: `CLAUDE_UI_OVERSIGHT_READY__CONSOLE_ARTIFACT_LANE`

## Lane role

Claude/UI owns the operator-facing console artifact posture: source-of-truth panels, agent lanes, review queue, doc explorer, AI-assist bubble behavior, builder action prompts, and maintenance-backend transition records. It is a control surface, not a shell executor.

## Source authority

| Source | Current value |
|---|---|
| Claude protocol | `D:\LightSpeed_Consolidated\_worktrees\LightSpeed-ls-go-launch-2026-06-07\.claude\ACHILLES_CLAUDE_PROTOCOL_2026-06-08.md` |
| Agent oversight index | `docs\agent-oversight\00_AGENT_OVERSIGHT_INDEX_2026-06-08.md` |
| Drive-backed console source | `[x] missing value: live Drive artifact source`; observed value: Google Drive connector `token_expired` 401 |
| Connected account | `[x] missing value: verified connected Drive account in this run`; observed value: connector `token_expired` 401 |

## Required checks

- The console must label connector/tool status visibly.
- Every panel must use concrete source values or `[x] missing value` rows.
- Builder actions draft only until authenticated write channels and explicit approval exist.
- Per-agent lanes must map to Achilles Core, Co-Runner, Desktop Codex, Terminal Codex, Claude/UI, and Local Runners.
- Persisted UI state must not contain credentials or secret values.

## Output contract

- `run_label`
- `ui_panels_reviewed`
- `agent_lanes`
- `build_prompts_prepared`
- `missing_values`
- `blocked_actions`
- `next_handoff`

## Hard stops

- No claim that UI changed live Drive/Squarespace/GitHub unless a verified connector/tool did it.
- No credential storage in localStorage, artifacts, or docs.
