# Agent Fileset Flow

## Purpose

This note captures current orchestration context for LightSpeed without creating Drive-equivalent archives inside Git.

## Correct flow

```text
Drive agent filesets
  -> LinkDrive source/original context
  -> LightSpeed Desktop pull/push layer
  -> Sheets control/state layer
  -> LightSpeed Web / achilles.romer presentation layer
  -> repo-backed public-safe components
```

## LightSpeed Desktop folders

LightSpeed Desktop should eventually have dedicated working folders for:

- LightSpeed
- De Sporte

These folders are for active information transfer and workspace/runtime use, not for creating another archive.

## Agent hierarchy context

- ACHILLES: internal and overarching orchestrator for Nathaniel Bouwer, Römer Industries, Cognigrex and system-wide operations.
- Neo: orchestrator role for LightSpeed Desktop and local execution flow.
- Athene: front-facing non-LightSpeed-Web public agent concept, originally reasoned before the current LightSpeed/Web application direction.
- EMASSC: no dedicated agent required yet; Athene may later become the internal-facing EMASSC-aligned agent.

## Boundary

This repo should define interfaces, adapters and local/web execution contracts. It should not become the canonical Drive archive.
