import { build } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

// Produces a portable HTML build of the actual game; no Cloudflare runtime or
// development-machine connection is needed by the GitHub rendering job.
await build({
  configFile: false,
  root: resolve("review"),
  publicDir: resolve("public"),
  plugins: [react()],
  resolve: { alias: { "next/dynamic": resolve("review/dynamic.tsx") } },
  css: { postcss: resolve("postcss.config.mjs") },
  build: {
    outDir: resolve("review-dist"),
    emptyOutDir: true,
    sourcemap: false,
    target: "es2022",
  },
});
