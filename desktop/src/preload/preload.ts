import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electronAPI", {
  platform: process.platform,
  getVersion: () => ipcRenderer.invoke("get-version"),
  openExternal: (url: string) => ipcRenderer.invoke("open-external", url),
});
