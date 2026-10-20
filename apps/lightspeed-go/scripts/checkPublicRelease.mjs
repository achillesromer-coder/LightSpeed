/*CGX UniSpace public-static distribution guard.

This intentionally checks known internal-review source routes in both Vite's
public/ source and compiled dist/. It does NOT authenticate user sessions,
qualify any catalogue as public, or prove all other assets are non-sensitive.
*/
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const defaultSite = path.resolve(here, "..");
export const HELD_EXACT = Object.freeze([
  "data/cgx_object_review_catalogue.json",
  "data/component_geometry_atlas_public_review.json",
]);
export const HELD_PREFIXES = Object.freeze([
  "review/renders/",
  "review/mesh/",
]);
function enumerate(directory, root, files, maxFiles = 50000) {
  if (!fs.existsSync(directory)) return;
  for (const part of fs.readdirSync(directory, { withFileTypes: true })) {
    const p = path.join(directory, part.name);
    if (part.isSymbolicLink()) {
      files.push({ route: path.relative(root, p).split(path.sep).join("/"), symlink: true });
    } else if (part.isDirectory()) {
      enumerate(p, root, files, maxFiles);
    } else if (part.isFile()) {
      files.push({ route: path.relative(root, p).split(path.sep).join("/"), symlink: false });
    }
    if (files.length > maxFiles) throw Error("BOUND_EXCEEDED: refuse unverifiable build");
  }
}
export function scanPublicRelease({ siteRoot = defaultSite, phase = "source" } = {}) {
  if (!["source", "dist"].includes(phase)) throw Error("unsupported phase");
  const root = path.join(siteRoot, phase === "source" ? "public" : "dist");
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    return { schema: "CGX-PUBLIC-DISTRIBUTION-GATE/0.1", phase,
      state: "HOLD_MISSING_DISTRIBUTION_ROOT", held_count: 0,
      known_disclosure_paths: [], build_authorised: false,
      public_release_authorised: false, complete_privacy_audit: false };
  }
  const paths = [];
  enumerate(root, root, paths);
  const held = paths.filter(({ route, symlink }) =>
    symlink || HELD_EXACT.includes(route) || HELD_PREFIXES.some(prefix => route.startsWith(prefix))
  ).map(x => ({ static_route: "/" + x.route,
    reason: x.symlink ? "SYMLINK_IN_STATIC_TREE" : "INTERNAL_OWNER_REVIEW_ASSET" }))
   .sort((a,b) => a.static_route.localeCompare(b.static_route));
  return { schema: "CGX-PUBLIC-DISTRIBUTION-GATE/0.1", phase,
    state: held.length ? "HOLD_KNOWN_STATIC_DISCLOSURE" : "NO_KNOWN_PATH_MATCH_UNVERIFIED",
    held_count: held.length, known_disclosure_paths: held,
    build_authorised: held.length === 0, public_release_authorised: false,
    complete_privacy_audit: false,
    still_required: ["source owner and rights allowlist", "built output source-byte diff",
      "unauthenticated/revoked/cross-tenant HTTP negative paths", "authenticated private review backend"] };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const opts = { siteRoot: defaultSite, phase: "source" };
  for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i] === "--phase" && process.argv[i+1]) opts.phase = process.argv[++i];
    else if (process.argv[i] === "--root" && process.argv[i+1]) opts.siteRoot = path.resolve(process.argv[++i]);
    else throw Error("Unknown argument");
  }
  const result = scanPublicRelease(opts);
  process.stdout.write(JSON.stringify(result,null,2)+"\n");
  if (!result.build_authorised) process.exitCode = 2;
}