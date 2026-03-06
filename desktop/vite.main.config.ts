import { defineConfig } from "vite";
import { getConfig } from "@electron-forge/plugin-vite/dist/config/vite.main.config";
import type { Plugin } from "vite";

function electronRestart(): Plugin {
  return {
    name: "electron-auto-restart",
    closeBundle() {
      // Forge listens for "rs\n" on stdin to restart the Electron process
      process.stdin.emit("data", "rs");
    },
  };
}

export default defineConfig((env) => {
  const config = getConfig(env as any);
  if (env.command === "serve") {
    (config.plugins ??= []).push(electronRestart());
  }
  return config;
});
