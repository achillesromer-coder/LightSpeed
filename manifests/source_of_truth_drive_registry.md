# Source-of-Truth Drive Registry

## Status

This file records the current Drive folder IDs supplied for ACHILLES / Römer-Coder orchestration.

The folders are treated as authoritative external source locations. This repo does not duplicate their full contents.

## Current Drive folders

| Folder ID | Role / treatment |
|---|---|
| `1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb` | Main Römer / LinkDrive source folder previously mapped as core business/source/evidence location. |
| `1eRmR6kkNimF-U6-r6bQI9C7pWskc27W9` | ACHILLES / LightSpeed / app-workflow and runtime-orchestration folder previously mapped with LightSpeed Desktop, MPL, logs and conversations. |
| `1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag` | Data / Raphael / empirical library source folder previously mapped with JSON library, physics, EMASSC and related source materials. |
| `1DdbvO2fsVk1I8T1B9dnxOFlvevnugt0g` | Main public / achilles.romer / target Drive folder for the new source-of-truth fileset and repo-linked orchestration. |

## Current authority model

```text
Drive source-of-truth folders
  -> LinkDrive / ACHILLES source and target filesets
  -> LightSpeed Desktop pull/push and runtime orchestration
  -> Sheets control/state/log/review layer
  -> GitHub repo scaffold and component files
  -> LightSpeed Web / achilles.romer public-safe presentation
```

## Repo rule

Repos should store schemas, manifests, component code, public-safe docs and orchestration contracts.

Repos should not become a duplicate Drive archive.

## Pull/push rule

- Pull source files from Drive only through registered manifests.
- Push repo-ready components, summaries, generated docs and review-gated outputs back to the correct Drive target.
- Record major events and task outcomes only.
- Avoid microtransactional log spam.
