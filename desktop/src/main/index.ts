import { app, BrowserWindow, dialog } from "electron";
import path from "path";
import { startBackend, stopBackend, getBackendPort } from "./backend";
import { showSplash, updateSplashStatus, closeSplash } from "./splash";
import { buildMenu } from "./menu";

process.on("uncaughtException", (err) => {
  console.error("[main] Uncaught exception:", err);
  dialog.showErrorBox("Unexpected Error", err.message);
});

let mainWindow: BrowserWindow | null = null;
let isQuitting = false;

const ELECTRON_DRAG_CSS = `
  /* Sidebar top area (logo) — draggable, leave room for traffic lights */
  .copaw-layout-sider > div:first-child {
    -webkit-app-region: drag;
    padding-top: 36px !important;
  }

  /* Header bar — draggable */
  .copaw-layout-header {
    -webkit-app-region: drag;
  }

  /* All interactive elements inside drag regions — exclude from drag */
  .copaw-layout-header button,
  .copaw-layout-header a,
  .copaw-layout-header .copaw-select,
  .copaw-layout-sider .copaw-menu,
  .copaw-layout-sider .copaw-menu-item,
  .copaw-layout-sider a {
    -webkit-app-region: no-drag;
  }
`;

function createMainWindow(port: number): BrowserWindow {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    trafficLightPosition: { x: 16, y: 16 },
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadURL(`http://127.0.0.1:${port}`);

  win.webContents.on("did-finish-load", () => {
    win.webContents.insertCSS(ELECTRON_DRAG_CSS);
  });

  win.once("ready-to-show", () => {
    closeSplash();
    win.show();
  });

  win.on("close", (e) => {
    if (!isQuitting) {
      e.preventDefault();
      win.hide();
    }
  });

  win.on("closed", () => {
    mainWindow = null;
  });

  return win;
}

async function bootstrap(): Promise<void> {
  buildMenu();
  showSplash();
  updateSplashStatus("Initializing...");

  try {
    updateSplashStatus("Starting backend...");
    const { port } = await startBackend((line) => {
      if (line.includes("Uvicorn running")) {
        updateSplashStatus("Almost ready...");
      }
    });

    updateSplashStatus("Loading interface...");
    mainWindow = createMainWindow(port);
  } catch (err) {
    console.error("[main] Failed to start:", err);
    updateSplashStatus("Startup failed. Check logs.");
    setTimeout(() => {
      closeSplash();
      app.quit();
    }, 3000);
  }
}

app.setName("CoPaw");

app.on("ready", bootstrap);

app.on("activate", () => {
  if (mainWindow) {
    mainWindow.show();
  } else {
    const port = getBackendPort();
    if (port) {
      mainWindow = createMainWindow(port);
    }
  }
});

app.on("before-quit", async (e) => {
  if (isQuitting) return;
  isQuitting = true;
  e.preventDefault();
  await stopBackend();
  app.quit();
});

app.on("window-all-closed", () => {
  // On macOS, don't quit when all windows are closed
  if (process.platform !== "darwin") {
    app.quit();
  }
});

