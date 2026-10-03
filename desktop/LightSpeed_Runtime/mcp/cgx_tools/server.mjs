#!/usr/bin/env node
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import * as z from "zod/v4";

const here = dirname(fileURLToPath(import.meta.url));
const bridgePath = join(here, "bridge.py");
const pythonCommand = process.env.CGX_PYTHON || "python";

function textResult(value) {
  return {
    content: [{ type: "text", text: JSON.stringify(value, null, 2) }],
  };
}

function runBridge(operation, args = {}, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    const child = spawn(pythonCommand, [bridgePath], {
      cwd: here,
      windowsHide: true,
      env: { ...process.env, PYTHONUTF8: "1" },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`CGX bridge timed out after ${timeoutMs} ms`));
    }, timeoutMs);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });
    child.on("error", error => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", code => {
      clearTimeout(timer);
      let payload;
      try {
        payload = JSON.parse(stdout || "{}");
      } catch (error) {
        reject(new Error(`Invalid CGX bridge JSON: ${error.message}; stderr=${stderr}`));
        return;
      }
      if (code !== 0 || payload.ok !== true) {
        reject(new Error(payload.message || stderr || `CGX bridge exited ${code}`));
        return;
      }
      resolve(payload.result);
    });

    child.stdin.end(JSON.stringify({ operation, args }), "utf8");
  });
}

const server = new McpServer({
  name: "lightspeed-cgx-tools",
  version: "0.1.0",
});

const readOnly = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
};

server.registerTool("cgx_get_capabilities", {
  description: "Return the real registered capability/shortcall state for one of the nine CGX selectors.",
  inputSchema: {
    selector: z.string().min(1).describe("Selector name, e.g. Raphael or Römer-Grex"),
  },
  annotations: { title: "CGX Capabilities", ...readOnly },
}, async ({ selector }) => textResult(
  await runBridge("capabilities", { selector })
));

server.registerTool("cgx_resolve_shortcall", {
  description: "Resolve a selector shortcall to its typed route, state, floors and toolkits without executing it.",
  inputSchema: {
    selector: z.string().min(1),
    shortcall: z.string().min(1).describe("Shortcall with or without leading slash"),
  },
  annotations: { title: "Resolve CGX Shortcall", ...readOnly },
}, async ({ selector, shortcall }) => textResult(
  await runBridge("resolve_shortcall", { selector, shortcall })
));

server.registerTool("cgx_resolve_object", {
  description: "Resolve a current CGX object/twin into child-domain identity, Operations binding, source owner and representation/evidence boundary. Read-only.",
  inputSchema: {
    query: z.string().min(1).describe("Object name, twin_id, semantic Object_ID, or known Operations object ID"),
    domain: z.enum(["romer", "eco", "emassc", "lightspeed"]).optional(),
  },
  annotations: { title: "Resolve CGX Object", ...readOnly },
}, async ({ query, domain }) => textResult(
  await runBridge("object_context", { query, domain })
));

server.registerTool("cgx_plan_cross_analysis", {
  description: "Build a bounded cross-analysis plan using context, minimum-sufficient-work and consequence preflight. Does not run tests or promote results.",
  inputSchema: {
    selector: z.string().min(1),
    question: z.string().min(1),
    domain_override: z.string().optional(),
    execution_depth: z.enum(["inspect", "propose", "simulate", "execute", "build", "publish"]).default("inspect"),
    reasoning_depth: z.string().default("standard"),
    cascade_class: z.enum(["C0", "C1", "C2", "C3", "C4"]).default("C0"),
    tags: z.array(z.string()).default([]),
    intent_payload: z.record(z.string(), z.unknown()).optional(),
    evidence: z.array(z.record(z.string(), z.unknown())).default([]),
  },
  annotations: { title: "Plan CGX Cross Analysis", ...readOnly },
}, async args => textResult(
  await runBridge("cross_analysis", args)
));

server.registerTool("cgx_consequence_preflight", {
  description: "Run typed assurance + custodial preflight for a declared domain/depth. Clearance is not execution permission.",
  inputSchema: {
    domain: z.enum(["romer", "eco", "emassc", "lightspeed"]),
    execution_depth: z.enum(["inspect", "propose", "simulate", "execute", "build", "publish"]),
    reasoning_depth: z.string().default("standard"),
    cascade_class: z.enum(["C0", "C1", "C2", "C3", "C4"]).default("C0"),
    tags: z.array(z.string()).default([]),
    assurance_assessment: z.record(z.string(), z.unknown()).optional(),
    custodial_assessment: z.record(z.string(), z.unknown()).optional(),
  },
  annotations: { title: "CGX Consequence Preflight", ...readOnly },
}, async args => textResult(
  await runBridge("preflight", args)
));
server.registerTool("cgx_plan_tool_extension", {
  description: "Determine whether a requested capability should reuse, alias, wrap, or implement the smallest typed adapter. Never installs automatically.",
  inputSchema: {
    selector: z.string().min(1),
    goal: z.string().min(1),
    desired_kind: z.string().default("auto"),
    requested_shortcall: z.string().optional(),
    required_capabilities: z.array(z.string()).default([]),
  },
  annotations: { title: "Plan CGX Tool Extension", ...readOnly },
}, async args => textResult(
  await runBridge("tool_plan", args)
));

server.registerTool("cgx_freecad_probe", {
  description: "Probe the registered local FreeCAD headless runtime and return version/availability without opening a document.",
  inputSchema: {},
  annotations: { title: "Probe FreeCAD", ...readOnly },
}, async () => textResult(
  await runBridge("freecad_probe")
));

server.registerTool("cgx_freecad_inspect", {
  description: "Read an FCStd document from registered project roots and return object tree, dimensions, placements and derived shape metadata. Read-only.",
  inputSchema: {
    path: z.string().min(1).describe("FCStd path inside D:/LightSpeed or the current user's Desktop"),
  },
  annotations: { title: "Inspect FreeCAD Document", ...readOnly },
}, async ({ path }) => textResult(
  await runBridge("freecad_inspect", { path }, 120000)
));

server.registerTool("cgx_freecad_bom", {
  description: "Return a derived read-only object/BOM summary from an FCStd document. Not an approved manufacturing/procurement BOM.",
  inputSchema: {
    path: z.string().min(1).describe("FCStd path inside registered project roots"),
  },
  annotations: { title: "Derive FreeCAD BOM", ...readOnly },
}, async ({ path }) => textResult(
  await runBridge("freecad_bom", { path }, 120000)
));

server.registerTool("cgx_bridge_health", {
  description: "Read the current LightSpeed bridge-health report from the existing local runtime.",
  inputSchema: {},
  annotations: { title: "LightSpeed Bridge Health", ...readOnly },
}, async () => textResult(
  await runBridge("health")
));

server.registerTool("cgx_list_receipts", {
  description: "List bounded LightSpeed result receipts from the registered Neo temp-shell result store.",
  inputSchema: {
    limit: z.number().int().min(1).max(100).default(50),
  },
  annotations: { title: "List LightSpeed Receipts", ...readOnly },
}, async ({ limit }) => textResult(
  await runBridge("receipts_list", { limit })
));

server.registerTool("cgx_open_receipt", {
  description: "Open one LightSpeed result receipt by result_id; no arbitrary filesystem path is accepted.",
  inputSchema: {
    result_id: z.string().min(1),
  },
  annotations: { title: "Open LightSpeed Receipt", ...readOnly },
}, async ({ result_id }) => textResult(
  await runBridge("receipt_open", { result_id })
));

server.registerTool("cgx_plan_local_work", {
  description: "Dry-run the existing supervised local workflow with heavy execution disabled. May create normal runtime planning receipts.",
  inputSchema: {
    instruction: z.string().min(1),
    task_id: z.string().optional(),
    project_id: z.string().optional(),
    receipt_target: z.string().default("neo"),
  },
  annotations: {
    title: "Plan Local CGX Work",
    readOnlyHint: false,
    destructiveHint: false,
    idempotentHint: false,
    openWorldHint: false,
  },
}, async args => textResult(
  await runBridge("local_plan", args, 180000)
));

server.registerTool("cgx_run_local_work", {
  description: "Execute the existing supervised local LightSpeed/Ollama workflow with heavy=false. Requires confirmed=true and never grants canonical/public authority.",
  inputSchema: {
    instruction: z.string().min(1),
    confirmed: z.literal(true).describe("Must be true only when local execution is intentionally requested"),
    task_id: z.string().optional(),
    project_id: z.string().optional(),
    receipt_target: z.string().default("neo"),
  },
  annotations: {
    title: "Run Local CGX Work",
    readOnlyHint: false,
    destructiveHint: false,
    idempotentHint: false,
    openWorldHint: false,
  },
}, async args => textResult(
  await runBridge("local_run", args, 300000)
));

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("LightSpeed CGX tools MCP running on stdio");
}

main().catch(error => {
  console.error("CGX MCP server error:", error);
  process.exit(1);
});
