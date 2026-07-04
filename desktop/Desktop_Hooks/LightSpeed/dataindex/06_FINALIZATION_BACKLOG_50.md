# LightSpeed Finalization Backlog (50)

Status date: 2026-04-02
Execution mode: desktop-first, reduction-first, non-destructive until replacement and verification are complete.

## 1-10 Runtime and duplicate bundle reduction

1. Reconcile the `runtime.py` delta between [lightspeed_runtime](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/lightspeed_runtime/runtime.py) and the Merovingian-hosted legacy bundle once the live rehome completes.
2. Reconcile the `desktop_adapters.py` delta between [lightspeed_runtime](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/lightspeed_runtime/desktop_adapters.py) and the Merovingian-hosted legacy bundle once the live rehome completes.
3. Remove compatibility-only live references to the legacy runtime bundle where `runtime` is already authoritative.
4. Replace remaining migration-first labels in the desktop shell with runtime-first labels.
5. Move any still-relevant legacy bundle notices into canonical operator docs.
6. Validate that all floor dependencies resolve through `runtime` first.
7. Declassify identical legacy bundle files as removal candidates.
8. Keep only differing legacy bundle files for temporary comparison until reconciled.
9. Generate a removal readiness checklist for the duplicate bundle.
10. Remove the duplicate bundle only after smoke, verify, and runtime regression checks remain green.

## 11-20 Generated data governance

11. Keep smart-floor data roots as the only canonical generated output roots.
12. Remove any duplicate generated exports from [data/generated](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/data/generated) and root legacy shells after reference checks.
13. Keep Merovingian [runtime_exports](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-4_Merovingian/data/runtime_exports) reporting-only and exclude it from tool summaries.
14. Continue compact index generation for every high-volume tool stream.
15. Add archive execution receipts for every staged and completed archive batch.
16. Add archive completion summaries by year and by batch.
17. Keep raw-run deletion disabled until archive receipts and review are complete.
18. Add publish package indexing alongside existing publish package outputs.
19. Move future test result artifacts into canonical generated-report paths.
20. Produce one generated-state report that operators can read without opening raw JSON trees.

## 21-30 Oracle and Morpheus consolidation

21. Keep Oracle as the mounted source browser and provenance surface.
22. Keep Morpheus as the canonical retrieval/search surface with previews.
23. Add richer preview support for selected text, JSON, and Python calculator assets.
24. Distinguish canonical, reference, and archive results more clearly in Oracle and Morpheus UI.
25. Reduce raw inspection panes in favor of concise operator cards.
26. Make dataset selection in TheConstruct draw directly from Oracle/Morpheus indexed sources.
27. Keep archive material searchable but visually de-prioritized.
28. Add direct jump actions from Oracle/Morpheus results into active Romer workflows.
29. Add filter presets for `NotebookLM`, calculators, Raphael, and archive-only sources.
30. Remove any remaining floor-local placeholder counters that duplicate runtime-backed counts.

## 31-40 Architect, Trinity, and Achilles operator flow

31. Keep Architect as the primary publish, package, and finalization surface.
32. Surface finalization status in the main workspace shell, not only in Architect.
33. Add explicit review actions for staged archive batches in Architect.
34. Add explicit completion actions for reviewed archive batches in Architect.
35. Keep Trinity and IT Portal as governed operator entrypoints, not separate logic owners.
36. Continue tightening IT Portal labels around operator flow, hygiene, and finalization.
37. Keep Neo as the approval-gated Achilles console.
38. Expand Achilles actions to cover archive review and package refresh flows.
39. Keep every non-trivial action approval-gated until later security hardening.
40. Reduce redundant planner wording where the actual runtime action model already exists.

## 41-50 File shuffle, cleanup, and final hardening prep

41. Inventory empty files and separate intentional markers from accidental empties.
42. Remove safe cache folders after each major integration pass.
43. Identify duplicate generated artifacts that are fully superseded by canonical paths.
44. Mark reference-only historical folders clearly before any move or deletion.
45. Prepare a safe file-shuffle map for docs, generated outputs, and legacy references.
46. Keep mounted external reservoirs outside the app tree; do not absorb them into source.
47. Refresh architecture and canonical map docs after each structural reduction pass.
48. Maintain smoke, verify, and runtime regression checks after every deletion candidate batch.
49. Prepare the final pre-hardening checklist for encryption, firewall, and access control work.
50. Freeze the canonical desktop structure only after duplicate bundle removal, archive governance, and UI/runtime alignment are complete.

## Current execution priority

- Complete the live rehome of `w6`, `operations/w6`, and `canonical_runtime` into smart-floor ownership.
- Continue the `oracle_ingest_file` archive batch lifecycle.
- Reduce compatibility-only runtime naming and references.
- Surface finalization state more prominently in the operator flow.
- Only then begin broader duplicate-file and empty-file cleanup.
