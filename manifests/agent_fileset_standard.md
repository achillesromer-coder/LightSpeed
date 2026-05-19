# Agent Fileset Standard

## Purpose

Define the minimum active fileset for each major AI/agent so Drive, Sheets, LightSpeed Desktop, LightSpeed Web and repo surfaces can converge around one operating pattern.

This is not an archive-expansion pattern. It is an active pull/push, navigation and interface-control pattern.

## Minimum package per major AI/agent

```text
<Agent>/
  <Agent>_Workbook.xlsx
  <Agent>_manifest.json
  README.md
  FLOW_AND_OPERATIONS.md
```

If an existing Drive package uses another spreadsheet naming convention, keep it in Drive and map it through the manifest.

## Workbook role

The workbook is the human-operable control and review surface.

Recommended tabs:

| Tab | Purpose |
|---|---|
| Landing | Agent identity, role, current status and primary links |
| Role_Architecture | Agent hierarchy, parent/sibling relationships and system purpose |
| Content_Navigation | Drive folders, Sheets, repo folders, web routes and active files |
| Primary_Function | Core operating responsibility |
| Secondary_Functions | Workspace/dataspace support functions |
| Active_Workspaces | Current `/operations/wn` links and status |
| Active_Dataspaces | Current `/wn/data` links and status |
| Event_Log | Major completed events and task milestones only |
| Open_Tasks | Active tasks, blockers and next decisions |
| Source_Register | Source packs, Drive files, sheets and repo references |
| Publication_Gates | Internal, restricted-index, review-gated, public-safe, published status |
| Bibliography_Index | Library-level references and citations |
| Appendix_Index | Supporting appendices and daughter-folder references |

## JSON manifest role

The JSON manifest is the machine-readable routing file.

It should define:

- agent id
- agent name
- primary role
- secondary roles
- parent agent
- sibling agents
- Drive folder references
- workbook reference
- linked repo paths
- active routes
- permitted input channels
- permitted output channels
- public/private status
- last sync

## README role

The README is the fast human orientation layer.

It should answer:

- What is this agent?
- What does it own?
- What does it not own?
- Where are its source files?
- Where are its repo files?
- What are its active routes?
- What are its stop gates?

## FLOW_AND_OPERATIONS role

This file explains operational flow:

```text
Drive source folder
  -> workbook and manifest
  -> LightSpeed Desktop pull/push
  -> Sheets state/control
  -> repo scaffold/component files
  -> LightSpeed Web or achilles.romer public-safe display
```

## Log rule

Do not micro-log every small transaction. Logs should capture major events, completed milestones, decisions, handoffs, review outcomes and blocked items.

## Library rule

Bibliography, index and appendix material should live at Library or daughter-folder level, not duplicated inside every internal subfolder.
