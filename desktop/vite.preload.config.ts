import { defineConfig } from "vite";
import { getConfig } from "@electron-forge/plugin-vite/dist/config/vite.preload.config";

export default defineConfig((env) => getConfig(env as any));
