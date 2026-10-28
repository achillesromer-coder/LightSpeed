# Eco.cgx qualified ecological alignment — additive review guard

**State:** GIT SOURCE ONLY / R1–R2 CANDIDATE. This file is an Eco-specific qualification adapter for the existing Cognigrex.cgx Family Set, not a replacement for the shared LOAD.cgx aligner, source registry, CCC router or native Resolve/DBR path.

## Evidence sources reviewed

- Existing `cgx/domain_templates/eco_semantic_library.json` (main Git blob `d4eac3fd93f8c85f0385718355b47d59556aa1ec`) distinguishes taxon, species, population, sample, observation, place, experiment and ecological state.
- Draft LOAD PR #205 `cgx/load_minimum/loadQualifiedKnowledge.mjs` (blob `7aa2d77ad026303ce28491e421ff1f836a309c2a`) checks type, dimensions, units, frame, configuration and epoch but has no ecological-specific taxon/specimen/observation context comparisons.
- Current Type 1 Eco-Grex Drive source manifest lists distinct Embedded Bio Blocks and Second Cycle originals. The field-data schema provides example device, site, observation, method, unit and temporal fields; its examples **are not observed ecological measurements**.
- The original EcoX control index retains a pending raw canonical workbook publication, uncompleted gates and no overarching-suite activation. This code does not depend on the missing workbook.
- Exact original GPT export shards 000–011 are not verified. A separate accessible `Conversations` folder has six large plain-text files (69–186 MB each) but no source-qualified equivalence to the requested shards; do not ingest these in this bounded run. The two folders `manual` and `manual-additions` inside `CGX Domain Skeletons 2026-09-21` are empty and are not evidence of an authoritative CGX MANUAL INTAKE.

## Contract

`planEcoAlignment` accepts explicitly permitted source and known-object IDs, rejects duplicate authorised IDs, discriminates subject/taxon/specimen/population/site/station identity, geospatial CRS and point, time, evidence class, method, units, measurement and environmental context. It marks missing mandatory observation metadata, including impossible calendar dates and unzoned timestamps. Geometry is a source-declared point only; no interpolation, CRS transform, inferred 3D, map reconstruction or environmental impact simulation.

Source-lineage review now distinguishes **overlapping permitted references**, **disjoint permitted references**, and **partially authorised reference sets**. Disjoint lineages produce `SOURCE_LINEAGE_DISJOINT_REVIEW`; filtered-out source references produce `NOVEL_SOURCE_SCOPE_PARTIAL` or `KNOWN_SOURCE_SCOPE_PARTIAL`. These are review warnings, not a prohibition on independently corroborated cross-source alignment. No unpermitted source ID or private source body is emitted. Provider ACL visibility does not by itself establish copyright, data reuse, or cultural stewardship rights.

All outputs are source-only. A typed alignment candidate never means the objects are identical, rights-cleared, measured, accepted or safe to release. Integration with the shared LOAD plan must remain a *review gate*, not a parallel source of canonical authority. No original source is copied into this repository.

## Reproduce

~~~sh
node --test cgx/domain_templates/eco_qualified_alignment.test.mjs
~~~

Forty declared Node regression cases cover distinct taxon/specimen/coordinates/evidence/time/method/environment/units, missing observation metadata, invalid coordinates, 3D vertical datum, permissions, duplicate IDs and no automatic native promotion. All 40 committed primary regression test bodies passed in an isolated V8 compatibility harness against the exact read-back module; this is **not a Node CI run or host acceptance**. A same-ID proof-priority regression was detected and corrected before the final passing run. These are **source-level negative tests**, not host, DBR, field or two-node tests.

## Native integration holds

Source rights/ACL and exact original byte hashes; GPT shard and manual-intake reconciliation; accepted current root and child; source-specific R1 reversible parse and loss report; scoped R2/Frontier/Overlay; independent DBR/root readback; issue #158 public static privacy; issue #161 two-node transfer if requested; ecological measurement and counterevidence before impact claims. No canonical write, installer, live solver or release.

## 2026-10-28 additional review gate

A declared observation timestamp such as `2026-02-29T12:00:00Z` (invalid calendar date), `2026-10-01T12:00:00` (no timezone) or an impossible UTC offset now yields `OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED`. Valid leap dates with explicit offsets remain candidates. This is a conservative R1/R2 timestamp qualification, not a conversion or native timestamp resolver. The 40 primary fixtures passed in an isolated V8 compatibility harness; Node CI and host/DBR acceptance must be checked separately.

## Coordinate-frame and unexecuted-QA qualification

A source-declared point geometry CRS and separately declared coordinate frame that disagree require `FRAME_CRS_RECONCILIATION_REQUIRED` until an explicit, source-backed transform relationship is reviewed; this adapter does not transform coordinates. An observation marked `Not run`, `untested` or `pending` cannot pass observation QA simply because values and identifiers are present. One pre-existing measurement-scope fixture incorrectly expected no differences despite deliberately disjoint source references; its positive fixture now uses an overlapping authorised source while separate disjoint-lineage tests remain intact. The complete proposed source-only suite contains **49 synthetic tests** (40 primary + 9 measurement scope). These are compatibility checks, not field evidence or native admission.
