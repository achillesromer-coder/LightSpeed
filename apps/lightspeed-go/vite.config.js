import { realpathSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vite";

// Keep the original Windows junction / physical source-root convergence.
// A visitor-only build uses the SAME LS GO codebase but never copies its private public/ assets.
export default defineConfig(({ mode }) => {
  const root = realpathSync(process.cwd());
  const reviewer = mode === "visitor";
  return {
    root,
    publicDir: reviewer ? false : "public",
    build: {
      outDir: reviewer ? "dist-review" : "dist",
      emptyOutDir: true,
      rollupOptions: {
        input: reviewer
          ? { reviewer: resolve(root, "review.html") }
          : { operator: resolve(root, "index.html"), reviewer: resolve(root, "review.html") },
      },
    },
  };
});
