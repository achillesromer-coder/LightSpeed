import { readFileSync } from "node:fs";
import { Script } from "node:vm";
import { test } from "node:test";
import assert from "node:assert/strict";

const html = readFileSync(new URL("../docs/romer-web-hooks/uos_universal_gateway_embed.html", import.meta.url), "utf8");
const script = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/)?.[1];
const list = script?.match(/var routes = \[([\s\S]*?)\n  \];/)?.[1];
const rows = [...(list || "").matchAll(/^\s*\["(\/[^"]+)", "([^"]+)", "([^"]+)", "([^"]+)", "(observed|historical|candidate)"\],?$/gm)];
const paths = rows.map((row) => row[1]);

test("inline gateway compiles without network imports", () => {
  assert.ok(script, "missing inline route resolver");
  assert.doesNotThrow(() => new Script(script));
  assert.doesNotMatch(script, /\bfetch\s*\(|\bWebSocket\s*\(|\bXMLHttpRequest\s*\(/);
  assert.doesNotMatch(script, /\blocalStorage\b|\bsessionStorage\b/);
  assert.doesNotMatch(script, /\beval\s*\(|\bFunction\s*\(/);
});

test("one unique public route per canonical URL, including proposed space and Grex pages", () => {
  assert.equal(rows.length, 37);
  assert.equal(new Set(paths).size, rows.length);
  for (const expected of [
    "/", "/aus", "/uos", "/cgx", "/cgx/load", "/cgx/fs", "/cgx/ds",
    "/cgx/ps", "/cgx/profile", "/cgx/ccc", "/cgx/cyc", "/cgx/doom",
    "/cgx/achilles", "/cgx/neo", "/cgx/athene", "/cgx/raphael", "/docs"
  ]) assert.ok(paths.includes(expected), "missing route " + expected);
});

test("URL is a non-authoritative selector; only visitor public descriptor can leave the page", () => {
  assert.match(script, /u\.origin !== window\.location\.origin/);
  assert.match(script, /rights: "public_metadata_only"/);
  assert.match(script, /authority: "none"/);
  assert.match(script, /execution_authorized: false/);
  assert.match(script, /peer_identity_verified: false/);
  assert.match(script, /signing_verified: false/);
  assert.match(script, /ternary_shape: "unresolved"/);
  assert.match(script, /button\.addEventListener\("click"/);
  assert.match(script, /cgx:public-route-discovered/);
});

test("embed is one self-contained, namespaced visual surface", () => {
  assert.match(html, /id="cgx-uos-gateway"/);
  assert.match(html, /data-mounted/);
  assert.match(html, /@media\(max-width:650px\)/);
  assert.match(html, /<style>/);
  assert.doesNotMatch(html, /<iframe|<script\s+src=/);
});
