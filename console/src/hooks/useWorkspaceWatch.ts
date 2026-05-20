/**
 * Subscribe to workspace file-change SSE stream.
 *
 * Re-uses the same fetch-based SSE pattern as Plan updates and Chat streaming.
 * No new npm packages required.
 *
 * Usage:
 *   useWorkspaceWatch((events) => { ... })
 *
 * `events` is an array of { change: "added"|"modified"|"deleted", path: string }
 */

import { useEffect, useRef } from "react";
import { workspaceApi } from "../api/modules/workspace";
import { buildAuthHeaders } from "../api/authHeaders";

export interface FileChangeEvent {
  change: "added" | "modified" | "deleted";
  path: string;
}

type FileChangeCallback = (events: FileChangeEvent[]) => void;

export function useWorkspaceWatch(
  onFileChange: FileChangeCallback,
  enabled = true,
): void {
  // Keep a stable ref so callers don't need to memoize the callback
  const callbackRef = useRef<FileChangeCallback>(onFileChange);
  callbackRef.current = onFileChange;

  useEffect(() => {
    if (!enabled) return;

    let active = true;
    const controller = new AbortController();

    async function connect() {
      const url = workspaceApi.getWatchUrl();
      let retryDelay = 1000;

      while (active) {
        try {
          const response = await fetch(url, {
            method: "GET",
            headers: buildAuthHeaders(),
            signal: controller.signal,
          });

          if (!response.ok || !response.body) {
            await sleep(retryDelay);
            retryDelay = Math.min(retryDelay * 2, 30_000);
            continue;
          }

          retryDelay = 1000; // reset on success
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          while (active) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";

            for (const line of lines) {
              if (!line.startsWith("data:")) continue;
              const raw = line.slice(5).trim();
              if (!raw) continue;
              try {
                const msg = JSON.parse(raw) as {
                  type: string;
                  events?: FileChangeEvent[];
                };
                if (msg.type === "file_change" && msg.events) {
                  callbackRef.current(msg.events);
                }
              } catch {
                // ignore parse errors
              }
            }
          }
        } catch (err) {
          if (!active) break;
          // AbortError = intentional disconnect
          if (err instanceof DOMException && err.name === "AbortError") break;
          await sleep(retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30_000);
        }
      }
    }

    void connect();

    return () => {
      active = false;
      controller.abort();
    };
  }, [enabled]);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
