import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const sample = "D:\\LightSpeed\\State\\Review\\FreeCAD_ADAPTER_20261003\\adapter_test.FCStd";
const client = new Client({ name: "cgx-freecad-proof", version: "0.1.0" }, { capabilities: {} });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [join(here, "server.mjs")],
  stderr: "pipe",
});
await client.connect(transport);
const inspectResult = await client.callTool({
  name: "cgx_freecad_inspect",
  arguments: { path: sample },
});
const bomResult = await client.callTool({
  name: "cgx_freecad_bom",
  arguments: { path: sample },
});
const parse = result => JSON.parse(result.content.find(x => x.type === "text").text);
const inspection = parse(inspectResult);
const bom = parse(bomResult);
console.log(JSON.stringify({
  passed: inspection.document.object_count === 2 && bom.row_count === 2,
  document: inspection.document,
  first_object: inspection.objects[0],
  bom_rows: bom.rows,
  inspection_evidence_class: inspection.evidence_class,
  bom_evidence_class: bom.evidence_class,
}, null, 2));
await client.close();
