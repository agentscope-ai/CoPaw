import { ChildProcess, spawn, execFileSync } from "child_process";
import fs from "fs";
import path from "path";
import http from "http";
import { app, dialog } from "electron";
import { getCopawBin, getWorkingDir, findFreePort, sleep, getRuntimeDir } from "./utils";

let backendProcess: ChildProcess | null = null;
let backendPort: number | null = null;
let logStream: fs.WriteStream | null = null;

function getLogPath(): string {
  const logsDir = path.join(app.getPath("userData"), "logs");
  fs.mkdirSync(logsDir, { recursive: true });
  const date = new Date().toISOString().slice(0, 10);
  return path.join(logsDir, `backend-${date}.log`);
}

function ensureRuntimeExists(): void {
  const copaw = getCopawBin();
  if (fs.existsSync(copaw)) return;

  const runtimeDir = getRuntimeDir();
  dialog.showErrorBox(
    "Runtime Not Found",
    `CoPaw Python runtime was not found at:\n${runtimeDir}\n\n` +
    `Please run the runtime preparation script first:\n` +
    `  bash desktop/scripts/prepare-runtime.sh`,
  );
  throw new Error(`Runtime not found at ${runtimeDir}`);
}

function ensureInitialized(): void {
  const configPath = path.join(getWorkingDir(), "config.json");
  if (fs.existsSync(configPath)) return;

  console.log("[backend] First launch — running copaw init...");
  const copaw = getCopawBin();
  try {
    execFileSync(copaw, ["init", "--defaults", "--accept-security"], {
      stdio: "inherit",
      timeout: 60_000,
      env: {
        ...process.env,
        COPAW_WORKING_DIR: getWorkingDir(),
      },
    });
    console.log("[backend] Initialization complete.");
  } catch (err) {
    console.error("[backend] Init failed:", err);
  }
}

function healthCheck(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(
      `http://127.0.0.1:${port}/api/version`,
      { timeout: 2000 },
      (res) => {
        resolve(res.statusCode === 200);
        res.resume();
      },
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

export interface BackendStartResult {
  port: number;
}

/**
 * Start the Python backend as a child process.
 * Runs `copaw init` on first launch, then `copaw app` on a free port.
 * Resolves when the health-check passes or rejects on timeout.
 */
export async function startBackend(
  onLog?: (line: string) => void,
): Promise<BackendStartResult> {
  ensureRuntimeExists();
  ensureInitialized();

  const port = await findFreePort();
  backendPort = port;
  const copaw = getCopawBin();

  logStream = fs.createWriteStream(getLogPath(), { flags: "a" });
  const timestamp = () => new Date().toISOString();

  logStream.write(`\n--- Backend starting at ${timestamp()} on port ${port} ---\n`);

  console.log(`[backend] Starting copaw app on port ${port}...`);

  backendProcess = spawn(copaw, ["app", "--host", "127.0.0.1", "--port", String(port)], {
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      COPAW_WORKING_DIR: getWorkingDir(),
    },
  });

  backendProcess.stdout?.on("data", (data: Buffer) => {
    const text = data.toString();
    logStream?.write(text);
    onLog?.(text);
  });

  backendProcess.stderr?.on("data", (data: Buffer) => {
    const text = data.toString();
    logStream?.write(text);
    onLog?.(text);
  });

  backendProcess.on("exit", (code, signal) => {
    const msg = `[backend] Process exited: code=${code} signal=${signal}`;
    console.log(msg);
    logStream?.write(`${msg}\n`);
    backendProcess = null;
  });

  const maxWait = 120_000;
  const interval = 1000;
  const deadline = Date.now() + maxWait;

  while (Date.now() < deadline) {
    if (!backendProcess) {
      throw new Error("Backend process exited unexpectedly during startup");
    }
    const ok = await healthCheck(port);
    if (ok) {
      console.log(`[backend] Backend ready on port ${port}`);
      return { port };
    }
    await sleep(interval);
  }

  throw new Error(
    `Backend did not become healthy within ${maxWait / 1000}s. ` +
    `Check logs at: ${getLogPath()}`,
  );
}

/**
 * Gracefully stop the Python backend.
 */
export async function stopBackend(): Promise<void> {
  if (!backendProcess) return;

  console.log("[backend] Stopping backend...");
  const proc = backendProcess;

  return new Promise<void>((resolve) => {
    const forceKillTimer = setTimeout(() => {
      console.log("[backend] Force killing backend...");
      proc.kill("SIGKILL");
      resolve();
    }, 5000);

    proc.on("exit", () => {
      clearTimeout(forceKillTimer);
      resolve();
    });

    proc.kill("SIGTERM");
  }).finally(() => {
    backendProcess = null;
    logStream?.end();
    logStream = null;
  });
}

export function getBackendPort(): number | null {
  return backendPort;
}

export function isBackendRunning(): boolean {
  return backendProcess !== null && !backendProcess.killed;
}
