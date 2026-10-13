import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const serverPath = fileURLToPath(new URL("../../../../tools/run_cgx_web_readonly_mcp.mjs", import.meta.url));
const client = new Client(
  { name: "cgx-web-readonly-test", version: "0.1.0" },
  { capabilities: {} },
);
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [serverPath],
  env: { ...process.env, CGX_MCP_EXPOSURE: "local" },
  stderr: "pipe",
});

try {
  await client.connect(transport);
  const listed = await client.listTools();
  assert.deepEqual(
    listed.tools.map(item => item.name).sort(),
    ["cgx_web_handshake"],
    "web exposure must not surface local action, filesystem, CAD or receipt tools",
  );
  assert.equal(listed.tools[0].annotations?.readOnlyHint, true);
  assert.equal(listed.tools[0].annotations?.destructiveHint, false);

  const response = await client.callTool({
    name: "cgx_web_handshake", arguments: {},
  });
  const message = response.content?.find(item => item.type === "text")?.text;
  assert.equal(typeof message, "string");
  const data = JSON.parse(message);
  assert.equal(data.schema_version, "cgx-web-tunnel-handshake-v1");
  assert.equal(data.parent_filespace, "Cognigrex.cgx");
  assert.equal(data.read_only, true);
  assert.equal(data.owner_session_verified, false);
  assert.equal(data.consumer_receipt_verified, false);
  assert.equal(data.canonical_write_authorized, false);
  assert.equal(data.git_commit_authorized, false);
  assert.equal(data.host_offline_inferred, false);
  assert.ok(["UNVERIFIED", "PUBLIC_BOOTSTRAP_CANDIDATE"].includes(data.local_bridge));
  assert.ok(!Object.keys(data).some(k => /secret|token|password|credential|absolute_path/i.test(k)));
  console.log(JSON.stringify({
    passed: true,
    exported_tools: listed.tools.map(item => item.name),
    handshake: data.schema_version,
    commit_enabled: false,
  }));
} finally {
  await client.close();
}
