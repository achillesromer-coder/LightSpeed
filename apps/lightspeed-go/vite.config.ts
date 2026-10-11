import {defineConfig} from "vite";
import {resolve} from "node:path";
export default defineConfig({
  build: {rollupOptions: {input: {
    operator: resolve(__dirname,"index.html"),
    reviewer: resolve(__dirname,"review.html"),
  }}},
});
