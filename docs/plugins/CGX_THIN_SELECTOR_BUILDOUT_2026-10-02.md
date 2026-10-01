# CGX thin-selector plugin buildout — implementation handoff

Date: 2026-10-02
Branch: `cgx/plugin-control-plane-2026-10-02`
Classification: additive interface/runtime scaffolding; no canonical promotion.

## Purpose

Expose ChatGPT/Codex as a low-friction operating surface over the existing
Cognigrex + LightSpeed system without creating a second runtime, application,
agent silo, filespace, or authority plane.

## Implemented in this pass

1. `cgx/domain_templates/plugin_selector_registry.json`
   - Defines Achilles, Neo, Athene, Raphael, Cognigrex, Römer-Grex, Eco-Grex,
     EMASSC and LightSpeed as thin routing selectors.
   - Binds domain selectors to the existing `domains.json` authority pattern.
   - Encodes no-parallel-runtime and current-Recovery invariants.

2. `plugins/source/schemas/cgx_context_envelope.schema.json`
   - Defines the stable context envelope passed from selector/intent resolution
     into the existing execution plane.

3. Shared skills
   - `cgx-selector`
   - `cgx-handshake`
   - `cgx-minimum-sufficient-work`

4. `desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_plugin_control.py`
   - Resolves selector aliases and domain defaults.
   - Resolves current accepted Recovery from live `domains.json`.
   - Fails closed if canonical verifier state is not PASS.
   - Chooses one of:
     - reuse existing;
     - reconcile explicitly compatible prior evidence;
     - execute missing discriminant only;
     - bounded new execution.
   - Builds `CGXContextEnvelope`.
   - Does not start a service or bypass existing supervisor/GO paths.

5. Unit tests
   - Selector normalisation.
   - Recovery fail-closed behavior.
   - Exact result reuse.
   - Explicit-only reconciliation.
   - Missing-discriminant execution.
   - Existing Neo/Achilles authority preservation.

6. Deterministic plugin package source
   - `plugins/source/selector_packages.json`
   - `plugins/source/build_plugin_packages.py`
   - One source definition generates nine selector packages.
   - The builder does not emit `mcp.json` until a real verified CGX MCP
     endpoint/transport is available.

## Intent simplification / minimum-work rule

Natural-language requests are translated into operation + subject + constraints
+ requested output + proof standard before execution routing.

Examples:

- "plant-based dairy-free snack" -> search subject `snack`; constraints
  `plant-based`, `dairy-free`; use provider filters where supported.
- "run/check this test" -> identify the intended test and current object/version;
  retrieve a valid current receipt first; run only if required.
- "compare these sweeps" -> verify compatibility, equations, units, boundaries
  and uncertainty; derive mathematically if valid; do not launch a mass sweep
  merely because the exact target point was not previously sampled.

## Deliberately not done

- No second MCP/application/runtime created.
- No Recovery carrier modified.
- No `domains.json` authority changed.
- No Drive canonical mutation.
- No main-branch merge.
- No arbitrary shell executor.
- No fabricated local endpoint or `mcp.json`.
- No hundreds of speculative skills generated from the corpus.

## Required next verification on the actual LightSpeed machine

1. Run:
   `python -m pytest desktop/LightSpeed_Runtime/tests/test_cgx_plugin_control.py`
2. Run the plugin package builder and inspect generated packages:
   `python plugins/source/build_plugin_packages.py`
3. Invoke the local `plugin-creator` skill against one generated selector
   package and compare its output/schema to the builder.
4. Resolve the actual supported local/hosted MCP transport for the existing
   LightSpeed bridge; wrap existing typed functions rather than exposing shell.
5. Add MCP verbs incrementally:
   `resolve_context`, `resolve_capabilities`, `plan_execution`,
   `resource_preflight`, `dispatch_workflow`, `get_receipt`,
   `submit_for_review`, then gated promotion operations.
6. Exercise selector × domain × reuse/reconcile/execute × light/heavy ×
   unavailable-local-model × invalid-Recovery × rejected-GO matrices.

## Promotion rule

Only after the actual machine tests and plugin-creator comparison pass should
this interface scaffold be considered for merge/promotion. Runtime receipts
remain evidence inputs, not automatic semantic truth.
