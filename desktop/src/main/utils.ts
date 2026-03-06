import { app } from "electron";
import path from "path";
import net from "net";

export function isDev(): boolean {
  return !app.isPackaged;
}

/**
 * Resolve the path to the bundled Python runtime.
 * - Dev: <project>/desktop/runtime/venv
 * - Packaged: <app>/Contents/Resources/runtime/venv
 */
export function getRuntimeDir(): string {
  if (isDev()) {
    return path.resolve(__dirname, "..", "..", "runtime");
  }
  return path.join(process.resourcesPath, "runtime");
}

export function getPythonPath(): string {
  return path.join(getRuntimeDir(), "venv", "bin", "python");
}

export function getCopawBin(): string {
  return path.join(getRuntimeDir(), "venv", "bin", "copaw");
}

export function getWorkingDir(): string {
  return path.join(app.getPath("home"), ".copaw");
}

/**
 * Find a free TCP port by briefly binding to port 0.
 */
export function findFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const addr = server.address();
      if (addr && typeof addr === "object") {
        const port = addr.port;
        server.close(() => resolve(port));
      } else {
        server.close(() => reject(new Error("Failed to get port")));
      }
    });
  });
}

/**
 * Sleep helper for async loops.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
