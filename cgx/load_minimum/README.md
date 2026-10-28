# LOAD.cgx — Alexandria minimum library entry (review)

This is a **source-only reviewed bootstrap**, not a new canonical root, accepted Object_ID, or release. The existing `Cognigrex.cgx` parent controls FileSpace identity and RootAuthority. LOAD is the requested shortest library activation alias for minimal offline identity/query and *permissioned* on-demand source hydration; do not use it to erase existing Alexandria IDs or source lineage.

**Scope:** use the existing S92 native child `EMBED` option on an isolated parent review copy; keep the prior accepted parent unchanged. Resolve the alias to an existing accepted identity before minting. Source forests are ingested and compared for reusable typed definitions, claims, models and capabilities; original content and competing opinions remain source-linked. Do not mirror NASA/GPT archives merely to satisfy a storage-size target.

**Local reference CLI:** `load_reader.py` provides inspect, resolve, search, walk, coverage and bounded hydrate metadata. The full prepared LOAD.cgx local review artifact is **not** committed to this public code branch, because it contains private provider locators and has no native admission authorization. The CLI is offline and nonexecuting by default. Source code is not verified installation.

**Hydration:** H0 identity/address; H1 relations; H2 source rights/provenance; H3 capability contract; H4 owner DBR/lease-gated execution (denied here). Geometry uses 12-face dodecahedral selector for view/addressing, never as identity authority. `unavailable`, `inaccessible`, `unknown` and `contested` remain distinct. Max per-work-unit 60 MiB, not an absolute data limit.

**Before accepting:** current host connected, exact original/accepted parent Object_ID and State/DBR roots read back; alias collision and rights checked; signed capability lease, privacy #158 and two-node #161 independently accepted where relevant. No automatic merge, file deletion, external publication, token issuance, physical action or privileged network fetch. See draft activation_contract.json.


## Selective semantic knowledge spread and viewport switching (review 2026-10-28)

The source-only portable implementation is now split into independent contracts:

- \`online_registry_projection_2026-10-28.json\` is a reproducible, 131-reference discoverable CGX/CCC catalogue, **not 131 admitted Object_IDs**. Its provider source registry Git blob IDs are tracked and the \`refreshLoadRegistry.mjs --check\` command detects drift.
- \`loadOnlineRegistry.mjs\` resolves exact source keys and creates child-scoped review hydration plans, without moving original source bodies or claiming online installation.
- \`loadSemanticViewport.mjs\` creates a permission-filtered semantic halo around one externally authorised focus Object_ID; matches new source claims to registered candidates without automatic identity merges; and switches among six UI viewport intents while preserving stable identity and evidence ceiling.
- \`semantic_viewport_contract.json\` maps \`document\` to the existing object inspector, \`3d\` to qualified \`twin-3d\`, \`chat\` to \`chat-generative\`, \`graph\` to \`topology-graph\`, \`interactive\` to read-only hybrid canonical cells and \`matrix\` to traceability.

**Separate user controls:** source/knowledge inclusion (\`max_nodes\`, \`max_evidence_refs\`), relationship depth (\`max_hops\`), cross-analysis breadth (\`max_cross_domains\`, \`max_cross_edges\`), reasoning depth (\`glance/standard/deep/audit/raw\`), device hydration (\`projection-lite/reader/editor/workstation/distributed\`), proposed execution depth (\`inspect/propose/simulate/execute/build/publish\`) and future host compute/transfer budgets (\`max_compute_ms\`, \`max_ops_per_second\`, \`max_transfer_bytes\`). A planning request for \`execute\` **does not execute**.

The field \`authorized_object_ids\` and \`authorized_source_ids\` **must** be explicitly supplied by the authenticated host. The planner refuses unauthorized focus, excludes inaccessible branches without disclosing their identity, and never increases evidence or rights through a view switch. A 3D view requires permitted source-linked geometry, a coordinate frame and units; an absent geometry becomes a Frontier requirement, not a fabricated 3D asset. A novel source name match is only \`SEMANTIC_MATCH_REVIEW\`; even matching source bytes do not prove equal semantic identities across observations, models, histories or owners.

### Integration sequence and tests

\`\`\`sh
node --test cgx/load_minimum/cgxLoadFeaturePlanner.test.mjs cgx/load_minimum/loadOnlineRegistry.test.mjs cgx/load_minimum/loadSemanticViewport.test.mjs
node cgx/load_minimum/refreshLoadRegistry.mjs --check
\`\`\`

UniSpace context-menu/wizard should call \`planFeature\` and \`planKnowledgeSpread\` / \`planViewportSwitch\` using the current accepted CGX identity and authorised per-device scope. The existing host's CCC application, rendering providers, compute queue and RootAuthority/DBR readback must be integrated **separately**. Nothing in this review branch demonstrates a fully deployed 3D/chat interactive runtime or installed large Alexandria corpus. Keep public/private source boundaries and the #158/#161 acceptance holds.
