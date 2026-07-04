# Misalignment Register

Generated: 2026-04-13T01:24:29+00:00
Owner: Trinity
Status: active implementation backlog

These are the next 25 implementation changes that appear missed, partially implemented, or misinterpreted across the current build.

## UX-MIS-001 - Project Wall

- Miss: Project component sets were present but the Bento grid behaved too much like one flat board.
- Change: Keep component-set and subfolder selection scoped inside the wall with visible breadcrumbs and tile filtering.
- Owner floor: Architect
- Priority: high

## UX-MIS-002 - Project Wall

- Miss: Static icons and smart widgets had different interaction language.
- Change: Use one action model: single click preview, double click open/run, right click grouped actions.
- Owner floor: Trinity
- Priority: high

## UX-MIS-003 - Preview

- Miss: Images, PDFs, maps, spreadsheets, datasets, and simulations were treated as generic binary files.
- Change: Expose preview modes and route native/full render work to the owning floor or OS viewer.
- Owner floor: Trinity
- Priority: high

## UX-MIS-004 - Z Floors

- Miss: Some floor tabs duplicated purpose, portal, and feature pages.
- Change: Keep each floor as one surface with purpose, feature/action list, inspector, and explicit full runtime routing.
- Owner floor: Trinity
- Priority: high

## UX-MIS-005 - Settings

- Miss: Startup, setup, theme, and page settings were still partially split by legacy entrypoint.
- Change: Route all supported edits through Smart Settings Hub focus sections.
- Owner floor: Trinity
- Priority: high

## UX-MIS-006 - Backgrounds

- Miss: Editable backgrounds were defined in contracts but not exposed as an operator control.
- Change: Expose base mode, gradient/color, uploaded picture path, environment reference, and scope.
- Owner floor: Trinity
- Priority: medium

## UX-MIS-007 - Holospace

- Miss: Holospace could be interpreted as a competing top-level mode/button.
- Change: Keep Workspace and Z Floor top-level; make Holospace a Construct-owned opt-in surface.
- Owner floor: TheConstruct
- Priority: medium

## UX-MIS-008 - Morpheus

- Miss: Review/search could drift into raw mentions instead of proofed definitions.
- Change: Prioritize dictionary, knowns, provenance, confidence, and source comparison before generic mention output.
- Owner floor: Morpheus
- Priority: high

## UX-MIS-009 - Oracle

- Miss: Original files and extracted components were not always visually separated.
- Change: Make Oracle the original-file holder and show extracted objects/tables/tasks as handoffs.
- Owner floor: Oracle
- Priority: high

## UX-MIS-010 - Z Direct

- Miss: Handoff receipts could look like loose files rather than stateful work packets.
- Change: Show received, updated, completed, deleted, and declassified states in one receipt table.
- Owner floor: Smith
- Priority: medium

## UX-MIS-011 - Neo

- Miss: Neo risked becoming another chat page instead of a front-facing operator.
- Change: Keep Neo as internal monologue, task proposer, proof requestor, and floor orchestrator.
- Owner floor: Neo
- Priority: high

## UX-MIS-012 - Achilles

- Miss: Achilles/Cognigrex oversight was implied but not always obvious in handoff flows.
- Change: Expose Achilles as approval-gated operator layer across Neo, Smith, and Architect.
- Owner floor: Neo
- Priority: medium

## UX-MIS-013 - Performance

- Miss: Heavy widgets and popups could be loaded at startup or in fragile windows.
- Change: Use compact summaries first, lazy-load heavy viewers, and prefer inline panels over popup stacks.
- Owner floor: Merovingian
- Priority: high

## UX-MIS-014 - Progress

- Miss: Long actions lacked clear progress/cancel states.
- Change: Add progress overlays for ingestion, diagnostics, simulation export, publishing, and dependency approval.
- Owner floor: Merovingian
- Priority: medium

## UX-MIS-015 - Dependencies

- Miss: Missing dependencies were treated as errors rather than queued approvals.
- Change: Create empty landing tables and queue Neo/Smith dependency approval with install command evidence.
- Owner floor: Smith
- Priority: medium

## UX-MIS-016 - Dictionary

- Miss: IT shorthand and floor abbreviations were requested but not yet complete as a searchable category.
- Change: Add IT category definitions and floor shorthand aliases into Oracle/Morpheus dictionary surfaces.
- Owner floor: Oracle
- Priority: medium

## UX-MIS-017 - Simulation

- Miss: GMAT and ephemeris outputs could be visible but not clearly replayable.
- Change: Attach simulation parameters, ephemerides, and rerun metadata to Construct artifacts.
- Owner floor: TheConstruct
- Priority: high

## UX-MIS-018 - Zoning

- Miss: Heliocentric zoning was specified but still needs richer UI hooks and shortlist export in the floor.
- Change: Expose zone summary, clusters, target shortlist, and GMAT batch export as Construct widgets.
- Owner floor: TheConstruct
- Priority: high

## UX-MIS-019 - Library

- Miss: Empirical/library content was condensed but still needs stronger proof-first browsing.
- Change: Show knowns, values, units, provenance, and confidence as primary columns, not raw file names.
- Owner floor: Oracle
- Priority: medium

## UX-MIS-020 - Controls

- Miss: Right-click availability varied by surface.
- Change: Back all context menus with typed action groups so every tile/page offers expected actions.
- Owner floor: Trinity
- Priority: medium

## UX-MIS-021 - Navigation

- Miss: Folder depth could still feel like external file browsing.
- Change: Add breadcrumbs and in-wall folder drilldown before falling back to OS folder open.
- Owner floor: Architect
- Priority: medium

## UX-MIS-022 - Data Tables

- Miss: Tables could be previewed but not yet fully edited like spreadsheet components.
- Change: Add row/cell editing, validation, save-as-datatable, and Morpheus proof status.
- Owner floor: Morpheus
- Priority: medium

## UX-MIS-023 - External Tools

- Miss: API/tool toggles exist but are not yet uniformly shown in compact smart menus.
- Change: Expose external tools toggle and API status through Settings Hub and each relevant floor action list.
- Owner floor: Trinity
- Priority: medium

## UX-MIS-024 - Publishing

- Miss: D-root publish destination should be snapshot-only and not a live work root.
- Change: Keep C-root as build/run source and add explicit overwrite snapshot packaging to D-root only at publish.
- Owner floor: Architect
- Priority: high

## UX-MIS-025 - Blank Release

- Miss: Generated user/project/company data can reappear after proof runs.
- Change: Add a release-clean command that clears runtime rows, project workspaces, and caches after final validation.
- Owner floor: Merovingian
- Priority: high
