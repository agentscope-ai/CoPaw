import type { ForgeConfig } from "@electron-forge/shared-types";
import { VitePlugin } from "@electron-forge/plugin-vite";
import path from "path";

const config: ForgeConfig = {
  packagerConfig: {
    name: "CoPaw",
    executableName: "CoPaw",
    icon: path.resolve(__dirname, "resources", "icon"),
    appBundleId: "com.copaw.desktop",
    darwinDarkModeSupport: true,
    osxSign: {},
    extraResource: [path.resolve(__dirname, "runtime")],
    asar: true,
  },
  makers: [
    {
      name: "@electron-forge/maker-zip",
      platforms: ["darwin"],
    },
    {
      name: "@electron-forge/maker-dmg",
      config: {
        format: "ULFO",
      },
    },
  ],
  plugins: [
    new VitePlugin({
      build: [
        {
          entry: "src/main/index.ts",
          config: "vite.main.config.ts",
          target: "main",
        },
        {
          entry: "src/preload/preload.ts",
          config: "vite.preload.config.ts",
          target: "preload",
        },
      ],
      renderer: [
        {
          name: "main_window",
          config: "vite.renderer.config.ts",
        },
      ],
    }),
  ],
};

export default config;
