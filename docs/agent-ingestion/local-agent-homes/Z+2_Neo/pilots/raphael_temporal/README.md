# Neo: Raphael temporal computation pilot

Scope: exactly one existing agent, **Neo** (Z+2_Neo). This is an isolated proof-of-contract; it does not modify LightSpeed, the host-local Cognigrex S92 carrier, UniSpace S91 carrier, other agents, Drive, or main. No model is started.

## Purpose and evidence discipline
The existing Raphael Paper II crosswalk provides conceptual axes 4D (event history), 5D (Frontier), 6D (candidate probabilities), 7D (counterfactual/replay), 8D (shared relations) and 9D (constraints). This pilot implements a **narrow digital subset**: 4D sequential receipts, 7D simulated retrospective forks, event-triggered stillness, and explicit external merge gates. These are software operations; they do not prove physical retrocausality, additional physical dimensions, consciousness, or quantum foam.

## Interface
Provide a trusted SHA-256 function, e.g. \`text => createHash("sha256").update(text).digest("hex")\`, when constructing \`NeoTemporalPilot\`. Its input is canonical JSON text. Use \`advance({taskId,phase,payload,expectedSeq,branchId})\` with lifecycle:
\`retrieve → interpret → document → receipt → close\`.
Only \`retrieve\` requires \`source_ref\`; inferred claims are not auto-promoted. All receipts are **unsigned local proposals**, not native signed DBR receipts. \`rehydrate()\` returns a defensive readback.

\`fork({from,branchId,atSeq})\` creates an offset-history **simulation branch**. \`proposeMerge({source,target})\` returns dual tip hashes and task-level conflicts but never applies a merge. Promotion must be routed through the existing DBR three-way semantic merge, lease, rights, assurance, review and independently verified admission.

\`idleTick({signals})\` models quiet active monitoring without adding a canonical receipt. It is not an always-running agent or proof of persistence across process shutdown.

## Execute tests
\`\`\`sh
node --test docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/neo_temporal_pilot.test.mjs
\`\`\`

## Known limitations / expansion gates
1. Operates only in process memory; no durable storage or signed DBR. Actual restart/replay persistence needs an existing approved storage adapter.
2. Uses a host-supplied hash; the caller must ensure real SHA-256 and durable key/signature authority separately.
3. Coarse task-level merge detection, not semantic field-level reconciliation. It deliberately refuses to execute merges.
4. No network crawler, negative-space topology solver, X/E geometry, ternary adapter, model inference, or parallel runner in this minimal pilot. These attach only after this lifecycle is proven.
5. No autonomous rights promotion, external actions, or agent spawning. Follow Neo's dry-run-first and one-floor gates.

## Source alignment
- \`docs/agent-ingestion/local-agent-homes/Z+2_Neo/agent_manifest.json\`
- \`cgx/domain_templates/agent_runtime_contract.json\`
- \`cgx/domain_templates/cognigrex_parent_topology.json\`
- \`UniSpace/README.md\`

Test passes establish only bounded in-memory contract behaviour. Do not treat them as proof of local runtime connectivity, DBR signing, canonical admission or physically altered history.
