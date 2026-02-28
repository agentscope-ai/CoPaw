import { defineConfig } from "vite";
import { getConfig } from "@electron-forge/plugin-vite/dist/config/vite.renderer.config";
import path from "path";

export default defineConfig((env) =>
  getConfig(env as any, {
    root: path.resolve(__dirname, "src/renderer"),
    server: {
      port: 5199,
      watch: {
        ignored: ["**/runtime/**"],
      },
    },
    build: {
      rollupOptions: {
        input: path.resolve(__dirname, "src/renderer/index.html"),
      },
    },
    optimizeDeps: {
      exclude: ["runtime"],
      entries: ["src/renderer/index.html"],
    },
  }),
);
