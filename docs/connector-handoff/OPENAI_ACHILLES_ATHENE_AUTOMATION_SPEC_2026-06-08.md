# OpenAI Achilles / Athene Automation Spec â€” 2026-06-08

Result label: `OPENAI_AGENT_AUTOMATION_SPEC_READY__RUNTIME_CREDENTIAL_MISSING_EXPLICIT`

## Purpose

Define the future OpenAI Agents build lane with `[x] missing value: OpenAI runtime credential`; observed value: no approved secret mechanism provided in this pass.

## Agent lanes

| Agent | Scope | Current state | Next safe build artifact |
|---|---|---|---|
| Achilles | Governance, build oversight, repo/Drive/Squarespace alignment, approval records | Active operator oversight | Local Agents SDK design brief and eval checklist |
| Athene | Public-facing overlay, interface guidance, safe public automation | Deferred | Public overlay gate checklist; no hook until privacy/claim gates pass |
| Smith | Queue routing and dry-run receipts | Local LightSpeed Z-floor | Deterministic local receipt generator |
| Neo | Local Ollama bridge and operator briefing | Local LightSpeed Z-floor | One-session model routing guard |

## Minimal future Agents SDK contract

- Input: current handoff packet path, requested action, gate state, target surface.
- Output: structured action proposal with `allowed`, `blocked_reason`, `files_to_touch`, `commands_to_run`, and `human_confirmation_required`.
- Tools: local file summary, git branch status read, route status read, connector-auth status read.
- Forbidden tools: secret reads, Drive mutation, Gmail send, public publish, main merge, wallet/token/payment/IPFS activation.
- Evals: blocked-action test, no-secret-output test, PR-packet generation test, Drive-writeback plan test, Athene-deferred-overlay test.

## API key gate

Do not create or run an OpenAI API-backed agent until the OpenAI Developers connector/key flow is explicitly authorized and a key is provided through the proper secret mechanism. Never print, commit, or summarize secret values.

## Next safe implementation

After connector/key authorization, create a minimal local prototype under a separate branch or local prototype folder:

- `agent.py` for Achilles proposal generation.
- `main.py` for CLI-only smoke run.
- `evals/` for blocked-action and no-secret-output checks.
- `docs/prompt.md` with the static governance prompt.

Keep this separate from the current LS Go launch branch unless explicitly approved.

