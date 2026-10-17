/** Fail-closed static release gate: the reviewer build may contain only the public review shell. */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative, resolve } from "node:path";

const output = resolve("dist-review");
const files = [];

const crawl = (folder) => {
  for (const entry of readdirSync(folder)) {
    const full = join(folder, entry);
    if (statSync(full).isDirectory()) crawl(full);
    else files.push(relative(output, full).replaceAll("\\", "/"));
  }
};

crawl(output);

if (!files.includes("review.html")) throw Error("Missing reviewer entry");
if (files.includes("index.html")) throw Error("Owner/operator entry leaked into reviewer artifact");

const allowedStatic = new Set([".js", ".css"]);
const denied = files.filter((path) => {
  if (path === "review.html") return false;
  if (!path.startsWith("assets/")) return true;
  return !allowedStatic.has(extname(path).toLowerCase());
});
if (denied.length) {
  throw Error("Internal or unexpected public reviewer assets: " + denied.join(", "));
}

const forbiddenReferencePatterns = [
  /cgx_internal_review_projection\.json/i,
  /cgx_object_review_catalogue\.json/i,
  /component_geometry_atlas_public_review\.json/i,
  /(?:^|[/'"])data\//i,
  /review\/renders\//i,
  /(?:^|[/'"])models?\//i,
  /\.(?:obj|step|stp|stl|glb|gltf|blend|fbx|zip|cgx)(?:[?#"'\s]|$)/i,
  /X-LightSpeed-Owner-Confirmation/i,
  /ls-go-command-v2/i,
  /local_agent_cycle/i,
  /Cognigrex\.cgx/i,
  /LightSpeed_Runtime/i,
  /(?:[A-Z]:\\\\|file:\/\/)/i,
];

for (const file of files.filter((path) =>
  path === "review.html" || [".js", ".css"].includes(extname(path).toLowerCase())
)) {
  const content = readFileSync(join(output, file), "utf8");
  const matched = forbiddenReferencePatterns.find((pattern) => pattern.test(content));
  if (matched) {
    throw Error("Private/internal reference in reviewer build: " + file + " matched " + matched);
  }
}

const html = readFileSync(join(output, "review.html"), "utf8");
if (html.includes("src/main.ts") || html.includes("src/osShell.ts")) {
  throw Error("Owner shell in reviewer entry");
}

console.log(JSON.stringify({
  result: "PASS",
  release_scope: "VISITOR_STATIC_ONLY",
  file_count: files.length,
  files,
  allowlist: ["review.html", "assets/*.js", "assets/*.css"],
  private_catalogue_packaged: false,
  owner_shell_packaged: false,
}));
