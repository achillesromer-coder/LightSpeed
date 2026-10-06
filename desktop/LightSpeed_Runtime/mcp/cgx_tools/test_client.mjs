import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const serverPath = join(here, "server.mjs");

function parseText(result) {
  const text = result?.content?.find(item => item.type === "text")?.text;
  if (!text) throw new Error("tool returned no text JSON");
  return JSON.parse(text);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const client = new Client(
  { name: "lightspeed-cgx-tools-selftest", version: "0.1.0" },
  { capabilities: {} },
);
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [serverPath],
  stderr: "pipe",
});

await client.connect(transport);
const listed = await client.listTools();
const names = listed.tools.map(tool => tool.name).sort();
const expected = [
  "cgx_bridge_health",
  "cgx_consequence_preflight",
  "cgx_freecad_bom",
  "cgx_freecad_inspect",
  "cgx_femm_probe",
  "cgx_freecad_probe",
  "cgx_gmat_probe",
  "cgx_mpl_probe",
  "cgx_get_capabilities",
  "cgx_list_receipts",
  "cgx_open_receipt",
  "cgx_plan_cross_analysis",
  "cgx_plan_local_work",
  "cgx_plan_tool_extension",
  "cgx_resolve_object",
  "cgx_resolve_shortcall",
  "cgx_run_local_work",
  "cgx_runtime_productization",
].sort();
assert(JSON.stringify(names) === JSON.stringify(expected), "unexpected tool surface");

const capabilities = parseText(await client.callTool({
  name: "cgx_get_capabilities",
  arguments: { selector: "Römer-Grex" },
}));
assert(capabilities.selector === "romer-grex", "Unicode selector did not normalize");
assert(capabilities.shortcall_count >= 10, "Römer-Grex shortcall profile incomplete");

const cad = parseText(await client.callTool({
  name: "cgx_resolve_shortcall",
  arguments: { selector: "Raphael", shortcall: "/cad" },
}));
assert(cad.route_id === "cad.freecad", "Raphael /cad route mismatch");
assert(cad.route.state === "available", "FreeCAD read-only adapter was not promoted");

const watchtower = parseText(await client.callTool({
  name: "cgx_resolve_object",
  arguments: { query: "WatchTower", domain: "romer" },
}));
assert(watchtower.resolved_twin_id === "watchtower", "WatchTower twin resolution mismatch");
assert(watchtower.semantic_domain === "romer", "WatchTower domain resolution mismatch");
assert(watchtower.semantic_resolution.semantic_object_id === "WT-001", "WatchTower semantic identity mismatch");
assert(watchtower.operations_binding.current_record_id === "COM-1675", "WatchTower Operations binding mismatch");

const gmat = parseText(await client.callTool({
  name: "cgx_gmat_probe",
  arguments: {},
}));
assert(gmat.state === "prepared_not_activated", "GMAT probe state mismatch");
assert(gmat.execution_exposed === false, "GMAT execution must remain unexposed");

const femm = parseText(await client.callTool({
  name: "cgx_femm_probe",
  arguments: {},
}));
assert(femm.solver_exposed === false, "FEMM solve must remain unexposed");

const mpl = parseText(await client.callTool({
  name: "cgx_mpl_probe",
  arguments: {},
}));
assert(mpl.state === "prepared_not_activated", "MPL probe state mismatch");
assert(mpl.execution_exposed === false, "MPL execution must remain unexposed");

const freecad = parseText(await client.callTool({
  name: "cgx_freecad_probe",
  arguments: {},
}));
assert(freecad.available === true, "FreeCAD probe did not report available");
assert(String(freecad.version).includes("FreeCAD 1.0.2"), "Unexpected FreeCAD version");

const preflight = parseText(await client.callTool({
  name: "cgx_consequence_preflight",
  arguments: {
    domain: "romer",
    execution_depth: "inspect",
    cascade_class: "C0",
    tags: ["engineering"],
  },
}));
assert(preflight.automatic_execution === false, "preflight granted automatic execution");
assert(preflight.canonical_mutation === false, "preflight granted canonical mutation");

const extension = parseText(await client.callTool({
  name: "cgx_plan_tool_extension",
  arguments: {
    selector: "Raphael",
    goal: "inspect FreeCAD geometry and BOM",
  },
}));
assert(extension.decision === "reuse_or_alias", "FreeCAD extension decision mismatch");

const cross = parseText(await client.callTool({
  name: "cgx_plan_cross_analysis",
  arguments: {
    selector: "Raphael",
    question: "compare field assumptions",
    execution_depth: "simulate",
  },
}));
assert(cross.preflight.state === "domain_required", "Raphael cross-analysis guessed a domain");

const runtimeProductization = parseText(await client.callTool({
  name: "cgx_runtime_productization",
  arguments: { action: "status", slot: "selftest" },
}));
assert(runtimeProductization.authority === "status-only", "runtime productization status crossed authority boundary");
assert(runtimeProductization.slot === "selftest", "runtime productization slot mismatch");

const receipts = parseText(await client.callTool({
  name: "cgx_list_receipts",
  arguments: { limit: 3 },
}));
assert(typeof receipts === "object" && receipts !== null, "receipt list failed");

console.log(JSON.stringify({
  passed: true,
  tool_count: names.length,
  tools: names,
  unicode_selector: capabilities.selector,
  watchtower_object: watchtower.semantic_resolution.semantic_object_id,
  cad_state: cad.route.state,
  freecad_version: freecad.version,
  gmat_state: gmat.state,
  femm_state: femm.state,
  mpl_state: mpl.state,
  preflight_decision: preflight.decision,
  extension_decision: extension.decision,
  domainless_raphael: cross.preflight.state,
  runtime_productization_slot: runtimeProductization.slot,
}, null, 2));

await client.close();
