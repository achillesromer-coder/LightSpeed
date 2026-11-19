import { readFileSync } from "node:fs";
import { Script } from "node:vm";
import { test } from "node:test";
import assert from "node:assert/strict";

const html = readFileSync(new URL("../docs/romer-web-hooks/uos_universal_gateway_embed.html", import.meta.url), "utf8");
const script = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/)?.[1];
const list = script?.match(/var routes = \[([\s\S]*?)\n  \];/)?.[1];
const rows = [...(list || "").matchAll(/^\s*\["(\/[^"]*)", "([^"]+)", "([^"]+)", "([^"]+)", "(observed|historical|candidate|missing-404)"\],?$/gm)];
const paths = rows.map((row) => row[1]);

function boot(href) {
  const attributes = new Map();
  const events = [];
  const element = (tag) => ({
    tagName: tag,
    children: [],
    textContent: "",
    appendChild(child) { this.children.push(child); return child; },
    getAttribute(key) { return attributes.get(key) ?? null; },
    setAttribute(key, value) { attributes.set(key, value); },
    addEventListener() {},
  });
  const root = element("div");
  const url = new URL(href);
  const context = {
    window: {
      location: { href: url.href, origin: url.origin },
      dispatchEvent(event) { events.push(event); }
    },
    document: {
      getElementById(id) { return id === "cgx-uos-gateway" ? root : null; },
      createElement: element
    },
    navigator: {},
    URL,
    CustomEvent: class {
      constructor(type, opts) { this.type = type; this.detail = opts.detail; }
    }
  };
  new Script(script).runInNewContext(context, { timeout: 200 });
  return { descriptor: events.find((event) => event.type === "cgx:public-route-discovered")?.detail, root };
}

test("inline gateway compiles without network imports", () => {
  assert.ok(script, "missing inline route resolver");
  assert.doesNotThrow(() => new Script(script));
  assert.doesNotMatch(script, /\bfetch\s*\(|\bWebSocket\s*\(|\bXMLHttpRequest\s*\(/);
  assert.doesNotMatch(script, /\blocalStorage\b|\bsessionStorage\b/);
  assert.doesNotMatch(script, /\beval\s*\(|\bFunction\s*\(/);
});

test("one unique public route per canonical URL, including previously unconnected routes", () => {
  assert.equal(rows.length, 51);
  assert.equal(new Set(paths).size, rows.length);
  for (const expected of [
    "/", "/aus", "/green", "/green/future", "/green/embedded",
    "/green/second-cycle", "/gmat", "/mpl-engine", "/raphael", "/docs",
    "/uos", "/cgx", "/cgx/load", "/cgx/fs", "/cgx/ds", "/cgx/ps",
    "/cgx/profile", "/cgx/ccc", "/cgx/cyc", "/cgx/doom",
    "/cgx/achilles", "/cgx/neo", "/cgx/athene", "/cgx/raphael",
    "/w1-data", "/w2-data", "/w3-data", "/w4-data", "/w5-data", "/w6-data"
  ]) assert.ok(paths.includes(expected), "missing route " + expected);
  const missing = rows.filter((row) => row[1].startsWith("/w") && row[1].endsWith("-data"));
  assert.equal(missing.length, 6);
  assert.ok(missing.every((row) => row[5] === "missing-404"));
});

test("public route resolves without authenticating or running any command", () => {
  const current = boot("https://romer.industries/green/embedded");
  assert.equal(current.descriptor.route, "/green/embedded");
  assert.equal(current.descriptor.facet, "eco");
  assert.equal(current.descriptor.execution_authorized, false);
  assert.equal(current.descriptor.peer_identity_verified, false);
  assert.equal(current.descriptor.rights, "public_metadata_only");
  assert.equal(current.descriptor.ternary_shape, "unresolved");

  const home = boot("https://romer.industries/");
  assert.equal(home.descriptor.route, "/");
  const uppercase = boot("https://romer.industries/CGX/LOAD/");
  assert.equal(uppercase.descriptor.route, "/cgx/load");
  assert.equal(uppercase.descriptor.facet, "load");

  const virtualFacet = boot("https://romer.industries/uos/raphael");
  assert.equal(virtualFacet.descriptor.page_type, "virtual-facet");
  assert.equal(virtualFacet.descriptor.route_evidence, "candidate");
  assert.equal(virtualFacet.descriptor.authority, "none");

  const unavailable = boot("https://romer.industries/w3-data");
  assert.equal(unavailable.descriptor.route_evidence, "missing-404");

  const unknown = boot("https://romer.industries/random-private-path");
  assert.equal(unknown.descriptor.page_type, "unmapped");
  assert.equal(unknown.descriptor.authority, "none");
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
