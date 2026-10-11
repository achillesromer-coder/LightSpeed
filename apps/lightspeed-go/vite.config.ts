import {defineConfig} from "vite";
import {resolve} from "node:path";

/** One LS GO source tree, two explicitly different release artifacts.
 * visitor build has NO Vite publicDir: it cannot copy private meshes/catalogues.
 * Operator build remains local/internal and is NOT a public deployment artifact.
 */
export default defineConfig(({mode}) => {
  const visitorOnly = mode === "visitor";
  return {
    publicDir: visitorOnly ? false : "public",
    build: {
      outDir: visitorOnly ? "dist-review" : "dist",
      emptyOutDir: true,
      rollupOptions: {
        input: visitorOnly
          ? {reviewer: resolve(__dirname,"review.html")}
          : {
              operator: resolve(__dirname,"index.html"),
              reviewer: resolve(__dirname,"review.html"),
            },
      },
    },
  };
});
