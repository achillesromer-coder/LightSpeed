# LightSpeed Final Operator OS 3x50 Matrix

Canonical source: `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed`

Snapshot target: `D:\LightSpeed_Consolidated`

Policy:
- C-root remains the source of truth.
- D-root is overwritten only during publish/snapshot finalization.
- Do not create new feature pages when a bento widget, drawer, modal, context menu, or hosted action can carry the function.
- Keep original files Oracle-owned; move extracted components through Morpheus proofing and Z Direct queues.
- Preserve smoke, verify, and compact tests after every 10-task slice.

## Track A: Bento / UI / Trinity Operator Experience

1. Make the main landing page contract project-first: project -> component set -> artifact.
2. Audit current project/dashboard entrypoints and identify one canonical bento landing path.
3. Route duplicated project buttons into grouped project actions.
4. Ensure project subfolders/component sets can describe documents, tables, files, icons, smart previews, tasks, maps, and simulations.
5. Add or expose static icon tile metadata: icon, file type, attached file, double-click action.
6. Add or expose smart preview tile metadata: preview type, refit behavior, edit/open action.
7. Make side bento tabs context-aware in contract/UI labels.
8. Make each Z floor landing page say what widgets/components it owns.
9. Keep all floor landing actions grouped by workflow rather than scattered.
10. Add loading/progress text for startup and floor initialization where currently silent.
11. Update shortcuts in visible UI: Ctrl+S search, Ctrl+Shift+S settings, Ctrl+K advanced command palette.
12. Keep Ctrl+, only as compatibility if present; do not present it as primary settings shortcut.
13. Add visible mode dropdown language: Workspace, Operator, Review, Holospace, Publish, Settings.
14. Confirm WASD messaging appears only in Holospace/immersive contexts.
15. Add right-click/context-menu language for artifact actions where UI supports it.
16. Add disabled-action explanations for missing dependencies/tools.
17. Make missing optional tools create visible Neo/Smith task prompts instead of hidden failures where feasible.
18. Normalize all “settings”, “wizard”, and “theme” labels to the shared Trinity settings library.
19. Collapse any remaining duplicate settings entry labels in touched files.
20. Collapse any remaining duplicate theme entry labels in touched files.
21. Add background control labels: solid color, gradient, uploaded image, uploaded environment reference.
22. Add three base visual modes to settings-facing labels: minimal, balanced, futuristic gamelike.
23. Ensure drop-file-background wording is visual-reference-first, not forced heavy 3D.
24. Add loading indicator guidance to bento artifacts that invoke heavy jobs.
25. Tighten glass hierarchy: primary mode shell, secondary bento cards, tertiary status strips.
26. Make Oracle landing read like intelligence desk plus neural tree/search side menu.
27. Make Morpheus landing read like review desk and search engine.
28. Make Neo landing read like front-facing AI operator and lab orchestrator.
29. Make TheConstruct landing read like lab sandbox and map/simulation surface.
30. Make Architect landing read like governance and publish control.
31. Make Smith landing read like queue/router and dependency action surface.
32. Make Merovingian landing read like compact system table and health floor.
33. Make Trinity landing read like all-in-one smart settings/control center.
34. Add/refresh inline comments only where bento grouping behavior is non-obvious.
35. Avoid cosmetic-only code churn without contract/test value.
36. Run py_compile on touched UI files.
37. Run smoke after touching shell or floor loaders.
38. Add UI contract tests where stable string contracts exist.
39. Avoid adding new pages for empty views.
40. Prefer existing dialogs, modals, tabs, drawers, or bento sections.
41. Check startup/help text for consistency with the final control model.
42. Check IT Portal labels against owner-floor responsibilities.
43. Check floor portals for old migration wording.
44. Check bento widget labels for file/edit/preview/fullscreen clarity.
45. Check context actions use explicit verbs.
46. Check visual density defaults are balanced, not overbearing.
47. Check performance hints for long-running interactions.
48. Summarize exact files changed.
49. Report tests run and residual UI risks.
50. Return next recommended UI polish slice.

## Track B: Workflow / Z Direct / Performance / Dependency Control

1. Model Oracle original-file retention as a runtime contract.
2. Model ingestion outputs as components: strings, tasks, tables, definitions, partial objects, source links.
3. Ensure Morpheus proofing is represented as the review gate for extracted components.
4. Ensure Z Direct handoff states include queued, received, updated, completed, deleted, and declassified.
5. Ensure Smith jobs can represent missing dependency approval tasks.
6. Add or tighten contracts for progressive partial-object merging.
7. Add or tighten contracts for component-set assignment to projects.
8. Make handoff payloads include source floor, target floor, rationale, artifact refs, and owner.
9. Make handoff payloads compact enough for UI display.
10. Keep raw source paths behind provenance links.
11. Ensure long-running work routes through Smith rather than UI blocking.
12. Ensure activity counters summarize repeated logs with timestamps in table cells.
13. Ensure external tools toggle is represented in settings/API contracts.
14. Ensure missing dependency behavior is non-crashing and task-producing where possible.
15. Ensure simulation outputs are saved as revisable/shareable ephemeris artifacts where relevant.
16. Ensure bootstrap/runtime summaries mention C-root canonical and D-root snapshot.
17. Ensure runtime does not recreate flat `data/generated`.
18. Ensure publish/snapshot roots remain floor-owned.
19. Ensure finalization reports include IT dictionary and operator OS contract paths.
20. Ensure activity tables include compact source-event counts.
21. Add tests for operator OS runtime contract.
22. Add tests for IT dictionary runtime contract.
23. Add tests for finalization pack inclusion of new artifacts.
24. Add tests for shortcut/config contract changes.
25. Add tests for missing dependency task contract if implemented.
26. Run targeted runtime tests after each slice.
27. Run smoke after bootstrap-impacting changes.
28. Run verify after path/finalization changes.
29. Avoid broad recursive file sweeps inside archived roots.
30. Avoid generated artifacts unless runtime-owned and regenerated on demand.
31. Keep compatibility read paths but canonicalize outputs.
32. Remove dead helper code only with coverage.
33. Simplify duplicated normalizers where safe.
34. Keep finalization output compact.
35. Keep logs as ledgers/tables, not one-file-per-event.
36. Keep API/external tools optional at launch.
37. Keep failed optional integrations visible and recoverable.
38. Keep dependency install actions approval-gated through Neo/Smith.
39. Keep CPU/RAM-heavy jobs backgrounded or lazy.
40. Keep startup loading state understandable.
41. Check Smith router for progressive object and dependency task payloads.
42. Check governance ledgers for action class/owner consistency.
43. Check finalization overview for new artifact visibility.
44. Check closure readiness for no pending matrix tasks.
45. Check path ownership after new files.
46. Check config JSON parses.
47. Summarize exact files changed.
48. Report tests run and residual runtime risks.
49. Report any UI/data follow-up blockers.
50. Return next recommended framework slice.

## Track C: Oracle / Dictionary / Data / Simulation / Neo-Achilles

1. Expand IT dictionary terms where core shorthand is still missing.
2. Ensure floor shorthand records exist and are searchable.
3. Ensure modes are searchable in the IT dictionary.
4. Ensure controls are searchable in the IT dictionary.
5. Ensure handoff definitions are searchable in the IT dictionary.
6. Ensure data-model terms are searchable in the IT dictionary.
7. Ensure project/bento artifact terms are searchable in the IT dictionary.
8. Add category-addition queue semantics to dictionary contracts.
9. Ensure new dictionary categories route to Neo/Oracle/Morpheus/Smith.
10. Keep AI logs corroboration-only in dictionary/provenance language.
11. Ensure Oracle original-file records remain editable/attachable/project-assignable.
12. Ensure ingestion components can become datatable rows.
13. Ensure ingestion components can become object definitions.
14. Ensure ingestion components can become tasks.
15. Ensure ingestion components can become partial object data.
16. Ensure partial object data has merge/corroboration guidance.
17. Ensure Morpheus review payloads show proof basis and confidence.
18. Ensure Oracle knowns avoid mention-driven summaries.
19. Ensure neural tree/network terms map to Oracle intelligence desk behavior.
20. Ensure empirical catalog records are compact and source-backed.
21. Reduce duplicate metadata between Oracle and Construct outputs.
22. Ensure TheConstruct preserves ephemeris/simulation result metadata.
23. Ensure GMAT/zoning outputs stay publishable and provenance-backed.
24. Ensure map/chart/simulation artifact types appear in bento contracts.
25. Ensure Neo action proposals reference dictionary/knowns terms where helpful.
26. Ensure Achilles/Cognigrex terms stay clear: Neo is first contact, Achilles governs, Cognigrex executes through tools/floors.
27. Ensure all high-impact AI actions remain approval-gated.
28. Ensure external data/API material stays optional and provenance-labeled.
29. Ensure datatable validation and unit validation terms are present.
30. Ensure confidence/bellcurve/overlay terms remain operator-readable.
31. Add or tighten dictionary tests.
32. Add or tighten knowns/proofing tests.
33. Add or tighten dataset catalog tests.
34. Add or tighten zoning/simulation metadata tests.
35. Add or tighten Neo proposal contract tests if touched.
36. Keep tests targeted and fast.
37. Validate touched Python files compile.
38. Run Oracle/data targeted pytest.
39. Avoid new raw-path-first payload fields.
40. Avoid generating one-off report files for single facts.
41. Write/update live IT dictionary artifact when terms change.
42. Write/update live Oracle definition artifact when terms change.
43. Write/update live operator OS artifacts when data/UI contract changes.
44. Check Oracle output paths remain floor-owned.
45. Check Construct output paths remain floor-owned.
46. Check Architect publish paths remain floor-owned.
47. Summarize exact files changed.
48. Report tests run and residual data risks.
49. Report remaining source roots needing assimilation.
50. Return next recommended Oracle/data/simulation slice.
