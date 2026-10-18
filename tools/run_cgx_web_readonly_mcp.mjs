#!/usr/bin/env node
/*
 * Reviewed ChatGPT-web entry into the EXISTING LightSpeed stdio MCP server.
 * Forces web-readonly before importing the shared tool registrations.
 * Do not launch server.mjs directly as a web/tunnel command.
 */
process.env.CGX_MCP_EXPOSURE = "web-readonly";
await import(new URL("../desktop/LightSpeed_Runtime/mcp/cgx_tools/server.mjs", import.meta.url).href);
