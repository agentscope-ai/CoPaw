import { request } from "../request";
import { getApiUrl } from "../config";
import type { MdFileInfo, MdFileContent, DailyMemoryFile } from "../types";

const encodePathSegments = (path: string) =>
  path
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");

export const workspaceApi = {
  listFiles: () =>
    request<MdFileInfo[]>("/agent/files").then((files) =>
      files.map((file) => ({
        ...file,
        updated_at: new Date(file.modified_time).getTime(),
      })),
    ),

  loadFile: (filePath: string) =>
    request<MdFileContent>(`/agent/files/${encodePathSegments(filePath)}`),

  saveFile: (filePath: string, content: string) =>
    request<Record<string, unknown>>(
      `/agent/files/${encodePathSegments(filePath)}`,
      {
        method: "PUT",
        body: JSON.stringify({ content }),
      },
    ),

  // Workspace package download
  downloadWorkspace: async (): Promise<Blob> => {
    const response = await fetch(getApiUrl("/workspace/download"), {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(
        `Workspace download failed: ${response.status} ${response.statusText}`,
      );
    }

    return await response.blob();
  },

  // File upload functionality
  uploadFile: async (
    file: File,
  ): Promise<{ success: boolean; message: string }> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(getApiUrl("/workspace/upload"), {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Upload failed: ${response.status} ${response.statusText} - ${errorText}`,
      );
    }

    return await response.json();
  },

  listDailyMemory: () =>
    request<MdFileInfo[]>("/agent/memory").then((files) =>
      files.map((file) => {
        const date = file.filename.replace(".md", "");
        return {
          ...file,
          date,
          updated_at: new Date(file.modified_time).getTime(),
        } as DailyMemoryFile;
      }),
    ),

  loadDailyMemory: (date: string) =>
    request<MdFileContent>(`/agent/memory/${encodeURIComponent(date)}.md`),

  saveDailyMemory: (date: string, content: string) =>
    request<Record<string, unknown>>(
      `/agent/memory/${encodeURIComponent(date)}.md`,
      {
        method: "PUT",
        body: JSON.stringify({ content }),
      },
    ),
};
