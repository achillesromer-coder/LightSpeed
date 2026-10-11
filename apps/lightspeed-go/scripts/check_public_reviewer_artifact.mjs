/** Fail-closed static release gate: public reviewer build must not copy the internal LS GO catalogue. */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
const output = resolve("dist-review");
const files = [];
const crawl = (folder) => {
  for (const entry of readdirSync(folder)) {
    const full = join(folder, entry);
    if (statSync(full).isDirectory()) crawl(full);
    else files.push(relative(output, full).replaceAll("\\","/"));
  }
};
crawl(output);
if (!files.includes("review.html")) throw Error("Missing reviewer entry");
const forbiddenPaths = [
  /(?:^|\/)index\.html$/i,
  /(?:^|\/)data\//i,
  /(?:^|\/)review\/renders\//i,
  /(?:^|\/)models?\//i,
  /\.(?:obj|step|stl|glb|gltf|blend|fbx|zip|cgx|json)$/i,
];
const denied = files.filter(path => forbiddenPaths.some(pattern=>pattern.test(path))
  || (!path.startsWith("assets/") && path !== "review.html"));
if (denied.length) throw Error("Internal or unexpected public reviewer assets: "+denied.join(", "));
const html = readFileSync(join(output,"review.html"),"utf8");
if (html.includes("src/main.ts") || html.includes("src/osShell.ts")) throw Error("Owner shell in reviewer entry");
for (const file of files.filter(path=>path.endsWith(".js") || path.endsWith(".html"))) {
  const content=readFileSync(join(output,file),"utf8");
  if (/cgx_internal_review_projection\.json|cgx_object_review_catalogue\.json|X-LightSpeed-Owner-Confirmation|ls-go-command-v2|local_agent_cycle/.test(content))
    throw Error("Private runtime reference in reviewer build: "+file);
}
console.log(JSON.stringify({result:"PASS", release_scope:"VISITOR_STATIC_ONLY", file_count:files.length,files}));
