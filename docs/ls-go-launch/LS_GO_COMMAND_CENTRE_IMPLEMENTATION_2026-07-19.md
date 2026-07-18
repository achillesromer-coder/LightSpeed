# LS GO Command Centre Implementation — 2026-07-19

## Purpose

LS GO is reduced to a simple operator command centre rather than another comprehensive dashboard. It provides four views:

1. **Command** — Achilles-governed command composition and routing.
2. **Activity** — Desktop health, recent tasks, locally saved envelopes, and the public-safe Neo exchange.
3. **System** — cognigrex definition, agent-floor roles, execution path, and retained bounded twin context.
4. **Sources** — direct access to the LightSpeed Git repository, LS GO Drive queue, portfolio handoff, and public Römer surface.

A **cognigrex** is treated as a common noun: the coordinated whole formed by LS Web, LS GO, Desktop, GPTs, tools, agents, and human oversight working toward a bounded objective while retaining separate roles and accountability.

## Browser-to-Desktop path

LS GO targets a local bridge at:

```text
http://127.0.0.1:8765
```

Start it from the repository root on Windows:

```bat
tools\run_ls_go_bridge.cmd
```

Or directly:

```bash
python tools/run_ls_go_bridge.py
```

The bridge is loopback-only and allows the published LS GO origin plus local Vite preview origins. It does not expose credentials or private Drive data.

## Command contract

Schema:

```text
lightspeed-go-command-v1
```

Required invariants:

- `oversight_floor` is `Achilles`.
- `proof_required` is `true`.
- `public_safe` is `true`.
- target floor is one of the recognised agent floors.
- execution mode is `review` or `queue`.
- commands create reviewable task/job records; the public site cannot directly publish, pay, hold custody, expose secrets, or bypass human authority.

## Persistence and execution

Every accepted command is appended to:

```text
Z Axis/Z+2_Neo/data/actions/ls_go_command_queue.jsonl
```

When the Desktop database is available, the bridge also creates:

- one `tasks` row;
- one `ls_go_command` job;
- metadata linking the command ID, target floor, Achilles oversight, execution mode, and queue artifact.

If Desktop is offline, LS GO stores up to 30 command envelopes in browser local storage and allows the operator to resend, download, or copy them.

## Agent routing

The browser performs transparent first-pass routing:

- UI, site, design, visual → Trinity
- Git, code, build, schema, API, runtime → Smith
- sources, evidence, Drive, workbook, citations → Oracle
- proof, claims, conflicts, audit → Morpheus
- simulation, GMAT, physics, digital twins → TheConstruct
- mission, plan, architecture, dependencies → Architect
- health, diagnostics, monitoring → Merovingian
- coordination, queue, handoff, execution → Neo
- otherwise → Achilles

The operator may override the suggested target floor. Achilles remains the oversight floor regardless.

## Source authority

- **Drive:** evidence, workbooks, approvals, results, and durable review records.
- **Git:** implementation, schemas, tests, branches, and code receipts.
- **Desktop:** local execution, task/job state, files, and artifacts.
- **LS GO:** command input, status, bounded queue projection, and handoff.

## Deployment boundary

The Git implementation is complete on the feature branch, but `lightspeed-go.nathaniel-b.chatgpt.site` is not a Git-native deployment target exposed to the connected deployment tools. Updating that exact host requires its ChatGPT Site publish/edit path. Do not represent the Git commit as proof that the ChatGPT Site host has changed.

The same source can be built with:

```bash
cd apps/lightspeed-go
npm ci
npm run test
npm run build
```

The built static output is `apps/lightspeed-go/dist` and can be used for the existing manual/public-site publish step or a separate Git-integrated host.

## Acceptance checks

- TypeScript check passes.
- Browser routing tests pass.
- Desktop bridge Python compiles.
- Bridge API accepts valid commands and rejects missing Achilles oversight.
- Public site contains no API key, OAuth secret, wallet, token, payment, custody, or private Drive payload.
- The chatgpt.site host is verified separately after publishing.
