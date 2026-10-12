#!/usr/bin/env node
/** Public-safe CGX discovery, without execution, persistence of credentials or a listener. */
import { open, realpath } from "node:fs/promises";
import { basename, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { publicSkeleton, discoverCgx, observeLocal } from "../src/handshake.mjs";

const help = [
  "CGX public bootstrap (source candidate; npm registry release NOT published)",
  "Commands:",
  "  cgx discover                      Inspect only the existing LS GO loopback bridge",
  "  cgx observe [--samples N] [--interval-ms N]   Read-only observation phases",
  "  cgx seed                          Print a minimal public-safe Alexandria .cgx JSON",
  "  cgx seed --write [NAME.cgx]       Create an exclusive public skeleton in current folder",
  "  cgx help                          Print this help",
  "",
  "No public scanning, remote tunnel, DNS broadcast, GPS, telemetry, credentials,",
  "local job execution or installation occurs. Status does not prove a running",
  "Smith consumer; a signed leased result receipt is still required.",
].join("\n") + "\n";

const print = value => process.stdout.write(JSON.stringify(value, null, 2) + "\n");

function integerOption(args, key, fallback) {
  const pos = args.indexOf(key);
  if (pos < 0) return fallback;
  if (pos + 1 >= args.length || !/^\d+$/.test(args[pos + 1])) {
    throw new Error(key + " needs an unsigned integer");
  }
  return Number(args[pos + 1]);
}

async function writeSeed(filename = "alexandria.public.cgx") {
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.cgx$/.test(filename) ||
      filename !== basename(filename)) {
    throw new Error("CGX seed output must be a simple .cgx filename");
  }
  const cwd = await realpath(process.cwd());
  if (cwd.split(/[\\/]+/).some(segment => segment.toLowerCase() === "documents")) {
    throw new Error("CGX bootstrap may not write inside protected Documents");
  }
  const target = resolve(cwd, filename);
  if (!target.startsWith(cwd + sep)) throw new Error("output escapes working directory");
  // wx: fail rather than overwrite; no default writing to C:, D:, E: or the native root.
  const handle = await open(target, "wx", 0o600);
  try { await handle.writeFile(JSON.stringify(publicSkeleton(), null, 2) + "\n", "utf8"); }
  finally { await handle.close(); }
  print({ state: "NEW_PUBLIC_TEMPLATE_ONLY", filename, identity_created: false,
    host_session_restored: false, sharing_enabled: false });
}

export async function main(args = process.argv.slice(2)) {
  const [command = "help", ...flags] = args;
  switch (command) {
    case "help":
    case "--help":
      process.stdout.write(help);
      return;
    case "seed": {
      if (flags.length === 0) return print(publicSkeleton());
      if (flags[0] !== "--write" || flags.length > 2) throw new Error("unsupported seed options");
      return writeSeed(flags[1]);
    }
    case "discover":
    case "doctor": {
      if (flags.length !== 0) throw new Error("discover takes no options");
      return print({ schema_version: "cgx-minimum-discovery-v1",
        ...await discoverCgx(), public_skeleton_schema: publicSkeleton().schema_version });
    }
    case "observe": {
      const samples = integerOption(flags, "--samples", 3);
      const intervalMs = integerOption(flags, "--interval-ms", 1000);
      const allowed = ["--samples", "--interval-ms"];
      const reconstructed = [];
      for (const key of allowed) {
        const i = flags.indexOf(key);
        if (i >= 0) reconstructed.push(key, flags[i + 1]);
      }
      if (reconstructed.length !== flags.length) throw new Error("unknown observe option");
      return print(await observeLocal({ samples, intervalMs }));
    }
    default:
      throw new Error("Unknown CGX subcommand. Use 'cgx help'.");
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    process.stderr.write("CGX_BOOTSTRAP_ERROR: " + String(error.message || "invalid option") + "\n");
    process.exitCode = 2;
  });
}
