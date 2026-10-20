# UniSpace / CGX — Exact identity and library usage convergence
**20 October 2026 | Source-stage candidate | Parent: draft PR #182 | Runtime not deployed**

## Selected next fold
Keep original PR #177 open/draft. Stage its existing source files:
- `desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_object_context.py` Git blob `bd0b4fb79fe75a57807b941e79cca60300414f43`
- `desktop/LightSpeed_Runtime/tests/test_cgx_object_identity.py` Git blob `d8b2a558f1cbcc384eadd8758e8cbcdc74952f37`
- `desktop/source-manifest.json` Git blob `890349a7d30008e4394b905822ed3b09c516e3f4`

Git comparison found that the desktop source-manifest changes only `LightSpeed_Runtime/lightspeed_runtime/cgx_object_context.py`: 9233→9632 source bytes and corresponding exact SHA-256; no other tracked source entries changed in this original PR. The identity resolver matches canonical identity only on exact admitted aliases and returns ambiguity on duplicate exact matches. Natural-language inspection still uses the existing score-based resolver. This closes one source-level identity-false-match test, not live `Cognigrex.cgx` alias acceptance.

## Existing libraries are referenced, NOT republished as a second catalogue

`cgx/review/library_coverage_projection.py` reads the following *current* registries without rewriting them:
1. `file_type_conversion_registry.json` → 33 declared profiles; retain per-type support/gated/structure/metadata status.
2. `semantic_view_lens_registry.json` → 13 shared + 21 specialist = 34 distinct lenses.
3. `cross_domain_bridge_registry.json` → 8 typed relation types.
4. `toolkit_registry.json` → 12 toolkit families.
5. `plugin_capability_routes.json` → 49 declared routes; not proof of connected plugin or live runtime.
6. `corpus_inclusion_registry.json` → 54 semantic classes and 21 durable source owner families; preserve owner boundaries.
7. `alexandria_external_reference_intake_20261020.json` → 207 external source-linked game and engine list entries, **no game assets, no upstream licences inferred**.
8. `passive_edge_profile_registry.json` and `unispace_keyed_publication_candidate_20261020.json` → device tiers/rights and release gates, not installed nodes.

Output is reproducible JSON including SHA-256 and size for each input registry, the registered type and route names, source owner references, unresolved frontiers, rights and release notes. It is a transient snapshot to power **existing** Creator/Press file, library, module and lens inspectors. The projection is explicitly not a new authority registry, inventory executor, semantic promotion, signed package or public API.

## Activation and inter-domain bridge plan
| Surface | Reusable current source | Missing acceptance |
|---|---|---|
| Offline Alexandria and UniSpace Creator | CGX source references, R0, local packages, 34 viewer lenses | Known-baseline device reopen, actual distributable source licences |
| Web Press / file converter | 33 native type profiles and source envelopes | Per-adapter reversible R1 and loss-mapped R2/R3 benchmark; guarded adapters remain HOLD |
| Capability/plugin picker | 12 toolkits, 49 route declarations | Installed tool discovery, authorization, failure/negative paths, receipt readback |
| Tree of Life/game/external knowledge | 8 typed relation bridges, external game engine catalogue | Upstream licence, true Object_ID referent mapping, ABI/runtime tests |
| InterSol/five-module project compiler | Component atlas, CAD/Type1 technical views, #181 source planner | Actual native CAD, SI source dimensions, mass, load, logistics, safety |
| Node/mobile/shared workspace | #179 passive-edge profiles, node exchange, #173 and #176 draft owners | #161 signed independent peer, leases, rights and readback |
| Public site/visitor | #174, #172 draft sites/review workspace | #158 static/private separation, unauthenticated negative tests |
| Offline games/Wayback/NASA | Reference-only published source links and NASA catalogues | Rights, source binary, dependencies, device and functional tests |

## Archive resolution and semantic rewrite
On intake: preserve original bytes/sha/locator and owner; resolve exact content duplication separately from referent identity. If semantically overlapping claims conflict, retain both with source/temporal frame and a payoff-review receipt; no silent canonical rewrite. Generated/modeled meaning remains R3/unverified unless domain owner independently validates it. A format conversion's apparent semantic similarity is not a reversible native file conversion.

## Git and release gates
- This is a **stacked draft source PR based on #182**. The earlier #177 and #179–#181 reviews remain open and source history remains intact.
- Never merge to main or install desktop code before unit/pytest, source-manifest hash parity, existing CGX assurance and root/peer/security owner reviews.
- Source refactor/continuation must not trigger C:/D:, Drive canon, provider writes, package-public mirror, consumer token or external catalogue download.
- #158 and #161 remain open: prior CI does not establish production/public/phone/physical readiness.
- #173, #175 and #176–178 stay separate until their runtime/shared-manifest conflicts are manually reconciled on current main. No force-rebase or auto-merge.
- This stage does **not** claim completion of all possible media adapters, external libraries, game engines or scientific models.
