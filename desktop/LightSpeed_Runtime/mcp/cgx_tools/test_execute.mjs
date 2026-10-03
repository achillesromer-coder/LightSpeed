import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const client = new Client({ name: "cgx-exec-proof", version: "0.1.0" }, { capabilities: {} });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [join(here, "server.mjs")],
  stderr: "pipe",
});
await client.connect(transport);
const result = await client.callTool({
  name: "cgx_run_local_work",
  arguments: {
    instruction: "Local-only MCP execution proof. Confirm the shared CGX tool path can route one bounded task through the current LightSpeed/Ollama supervisor. Do not modify canonical state or external providers.",
    confirmed: true,
    task_id: "MCP-CGX-LOCAL-PROOF-20261003",
    project_id: "LightSpeed",
    receipt_target: "neo"
  }
});
const text = result.content?.find(item => item.type === "text")?.text;
if (!text) throw new Error("No execution receipt returned");
const receipt = JSON.parse(text);
console.log(JSON.stringify({
  status: receipt.status,
  workflow_id: receipt.workflow_id,
  complete_workflow: receipt.complete_workflow,
  floor_sequence: receipt.floor_sequence,
  next_gate: receipt.next_gate,
  receipt_path: receipt.receipt_path,
  canonical_promotion_authorized: receipt.canonical_promotion_authorized,
  public_publish_authorized: receipt.public_publish_authorized
}, null, 2));
await client.close();
