# UX Amalgamation Pass

Generated: 2026-04-12
Owner: Trinity
Status: active walkthrough register

## Implemented This Pass

- Bento tiles now use the artifact interaction model: single click previews, double click opens/runs, Enter/Space opens/runs, arrow keys move between tiles.
- Bento right-click actions are grouped: Preview, Open / Run, Favorite, Set Active Floor, Open Owning Floor, Copy Widget ID, Copy Title.
- The shell now has a global right-click context menu for Search, Command Palette, Settings, Workspace routing, Z Floor routing, Back, and Help.
- F11 toggles fullscreen using the standard desktop convention.
- IT Portal keeps lightweight lazy floor shells instead of eagerly loading heavy floor runtimes.
- Project selection now opens a Bento component wall with default project folders, Z Direct staging, smart floor widgets, static icon tiles, file tiles, single-click preview, double-click open, keyboard open, and right-click target actions.
- Project file imports now preserve duplicate filenames with numbered targets so artifact tiles do not silently overwrite earlier source files.
- Project wall artifacts now support near-fullscreen preview/edit for text, markdown, JSON, CSV/TSV, code, SQL, GMAT, and ephemeris-style files; binary/native files retain explicit external open.
- Project wall context menus and the inspector now queue selected artifacts into Z Direct staging receipts for target smart floors.
- Selected Bento project tiles now show an active focus state so the operator can see which artifact the inspector and actions target.
- Project wall now includes a manifest-backed Floor Palette that exposes enabled smart-floor components, services, and capabilities as addable project widgets.
- IT Portal dashboard now uses a compact DB-backed recent-activity panel at startup instead of eagerly loading the heavier activity widget.
- IT Portal Z-floor tabs now use one single-surface smart-floor shell with purpose, feature/action list, inspector, manifest-backed Bento-style actions, and settings callaways instead of nested floor notebooks.
- Startup and autostart policy now runs through `lightspeed_runtime.startup_options`, is visible in each floor shell, and has a Trinity Settings Hub section for supported global startup toggles.
- Project wall component-set selection now scopes the visible Bento grid, reducing the flat-board feel and making folders/subfolders more operational.
- Project wall previews now identify image, PDF, map, spreadsheet, dataset, simulation, table, text, JSON, folder, and metadata modes.
- Project wall context menus now read grouped action availability from `artifact_action_groups` so tile actions are model-backed instead of UI-only.
- Trinity Settings Hub now includes a Background Builder for theme mode, gradient/color, uploaded picture path, environment reference, and application scope.
- The next 25 missed/misinterpreted implementation items are recorded in `dataindex/14_MISALIGNMENT_REGISTER.md` and Trinity UI data.

## Double-Ups Amalgamated

- Settings, themes, setup wizard, and page-local controls are treated as one Trinity settings library called from first-run, Ctrl+Shift+S, page menus, and widget settings.
- Holospace is not a competing top-level button. Workspace remains default; Construct/Holospace is opt-in for simulation or immersive contexts.
- IT Portal floor pages are not separate heavy runtime pages. They are lightweight navigation shells with full runtime opening only when explicitly requested.
- Bento actions are not extra feature pages. They resolve to widget callbacks, host actions, or owning-floor routing.
- Smart-floor functions are exposed from floor manifests into the project wall instead of duplicated as standalone feature pages.
- Heavy dashboard widgets should be explicit drill-ins; startup panels show compact summaries first.
- Startup, autostart, and launch controls are no longer treated as separate wizard-only surfaces. Trinity reads the runtime profile, Smith owns automation budget visibility, and Merovingian owns health/audit evidence.

## Role 3 Alignment Contract

- Primary surface: the user-facing project Bento wall stays the default operator OS. New chart, map, simulation, document, and floor actions must bind into this wall, a preview drawer, or an explicit fullscreen drill-in instead of creating new feature pages.
- Project workflow: select project -> component set -> subfolder/artifact group -> document/table/file/widget preview -> edit/fullscreen/handoff. Folder and subfolder tiles filter in place and must keep breadcrumb/back state visible.
- Document defaults: single click selects and previews, double click opens the best editor/viewer, Enter/Space activates the selected tile, Escape closes drawers/overlays first, right click shows grouped actions by availability.
- Z-floor access: there is one visible Z-floor dropdown / active-floor handoff route. Page-local buttons can call this route but should not add duplicate floor launchers or top-level floor pages.
- Theme/background controls: Trinity Settings owns base theme, background mode, color tokens, gradients, uploaded image path, environment reference, scope, preview, apply, and reset. Changes must propagate to shell, Bento wall, smart-floor shells, preview drawers, chart panels, maps, and simulation panels.
- Loading bars: startup, floor activation, ingestion/indexing, duplicate-safe file import, dependency checks, simulation runs, and publish/export packaging need queued/loading/running/blocked/complete/failed/cancelled states with owner floor, stage label, determinate percent when known, cancel availability, and fallback text.
- Dynamic widgets: smart-floor chart/map/simulation descriptors are renderer contracts. Each live tile needs id, owner floor, title, source artifacts, renderer, loading/empty/error states, fullscreen action, and handoff actions.

## Missing Interactive Elements

- Project folder bento wall depth: initial wall, subfolders, file tiles, smart widgets, in-panel text/table editing, and Z Direct handoff receipts are in place; next pass should add richer visual previews for PDFs/images/maps/simulations.
- Near-fullscreen artifact preview: text/table artifacts are implemented; next pass should add non-blocking media/PDF/map preview renderers.
- Background builder: theme colors and gradients are configured; uploaded image/environment preview and per-page assignment still need visible controls.
- Loading/progress overlays: long ingestion, floor runtime open, dependency approval/install requests, simulation export, and publishing should show progress/cancel states.
- Visual neural library desk: dictionary/search data exists; Morpheus still needs the neural graph/search-desk visualization layer.
- Page-local action menus: global context exists; individual doc/table/project tiles still need type-specific action submenus.
- Visual affordance polish: add hover/focus rings, selected tile state, and consistent active-floor color chips across all Bento/floor shells.

## Next UX Targets

- Extend the project component wall with PDF/image/map/simulation preview renderers without adding separate feature pages.
- Add a reusable preview drawer component for document, table, map, simulation, and file artifacts.
- Route all remaining standalone setup/theme/template buttons into the Trinity settings library without adding pages.
- Add progress overlays to Oracle ingestion, Smith jobs, Construct simulations, Merovingian diagnostics, and publish packaging.
- Bind the single Z-floor dropdown to page-local tile actions, active-floor chips, and Z Direct receipts so floor functions read as handoffs instead of competing pages.
- Wire Trinity Background Builder values into chart, map, simulation, and preview surfaces, not only the shell frame.
