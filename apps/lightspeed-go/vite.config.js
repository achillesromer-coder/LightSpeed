import { realpathSync } from "node:fs";
import { defineConfig } from "vite";

// Windows junctions preserve D:\LightSpeed as the operator namespace while
// resolving source files to their physical C: backing path. Give Vite one
// physical root so emitted asset names remain relative and portable.
export default defineConfig({
  root: realpathSync(process.cwd()),
});
