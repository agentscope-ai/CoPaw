/**
 * ProjectSelectModal
 *
 * Shown when the user first enters Coding Mode (or clicks "Switch Project").
 * Four tabs:
 *   1. Default Workspace  – use the agent's default workspace_dir
 *   2. Clone Repository   – git clone a public URL with SSE progress
 *   3. Open Local Path    – enter an absolute path
 *   4. New Project        – create an empty dir + git init
 */

import { useState, useRef } from "react";
import { Modal, Tabs, Input, Button, Alert, Progress, List, type InputRef } from "antd";
import { FolderOpen, GitBranch, HardDrive, PlusCircle, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { codingProjectApi, type ProjectListItem } from "../../api/modules/codingProject";
import { useProjectDir } from "../../stores/codingModeStore";
import FolderPicker from "./FolderPicker";
import styles from "./index.module.less";

interface ProjectSelectModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (path: string | null) => void;
}

// ---------------------------------------------------------------------------
// Clone progress event
// ---------------------------------------------------------------------------

interface CloneEvent {
  type: "log" | "done" | "error";
  line?: string;
  path?: string;
  name?: string;
  detail?: string;
}

// ---------------------------------------------------------------------------
// Tab: Workspace
// ---------------------------------------------------------------------------

function WorkspaceTab({
  currentProjectDir,
  onSelect,
}: {
  currentProjectDir: string | null;
  onSelect: (path: null) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className={styles.tabContent}>
      <Alert
        type="info"
        showIcon
        message={t("codingMode.workspaceDesc")}
        className={styles.workspaceAlert}
      />
      {currentProjectDir && (
        <div className={styles.currentInfo}>
          <span className={styles.currentLabel}>{t("codingMode.currentProject")}:</span>
          <code className={styles.currentPath}>{currentProjectDir}</code>
        </div>
      )}
      <Button type="primary" onClick={() => onSelect(null)} className={styles.actionBtn}>
        {t("codingMode.confirmBtn")}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Clone
// ---------------------------------------------------------------------------

function CloneTab({ onDone }: { onDone: (path: string) => void }) {
  const { t } = useTranslation();
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [cloning, setCloning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const handleClone = async () => {
    if (!url.trim()) return;
    setCloning(true);
    setLogs([]);
    setError(null);

    try {
      const res = await codingProjectApi.cloneStream(url.trim(), name.trim() || undefined);
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.startsWith("data: ") ? part.slice(6) : part;
          if (!line.trim()) continue;
          try {
            const evt: CloneEvent = JSON.parse(line);
            if (evt.type === "log" && evt.line) {
              setLogs((prev) => {
                const next = [...prev, evt.line!];
                setTimeout(() => logEndRef.current?.scrollIntoView(), 0);
                return next;
              });
            } else if (evt.type === "done" && evt.path) {
              setCloning(false);
              onDone(evt.path);
              return;
            } else if (evt.type === "error") {
              setError(evt.detail ?? "Unknown error");
              setCloning(false);
              return;
            }
          } catch {
            // ignore non-JSON lines
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setCloning(false);
    }
  };

  return (
    <div className={styles.tabContent}>
      <label className={styles.fieldLabel}>{t("codingMode.cloneUrl")}</label>
      <Input
        placeholder={t("codingMode.cloneUrlPlaceholder")}
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={cloning}
        className={styles.input}
      />
      <label className={styles.fieldLabel}>{t("codingMode.cloneName")}</label>
      <Input
        placeholder={t("codingMode.cloneNamePlaceholder")}
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={cloning}
        className={styles.input}
      />
      {error && <Alert type="error" message={error} className={styles.alert} showIcon />}
      {logs.length > 0 && (
        <div className={styles.logBox}>
          {logs.map((l, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <div key={i} className={styles.logLine}>
              {l}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      )}
      {cloning && <Progress percent={99} status="active" size="small" className={styles.progress} />}
      <Button
        type="primary"
        onClick={() => void handleClone()}
        loading={cloning}
        disabled={!url.trim()}
        className={styles.actionBtn}
      >
        {cloning ? t("codingMode.cloning") : t("codingMode.cloneBtn")}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Open Local Path
// ---------------------------------------------------------------------------

function LocalPathTab({ onSelect }: { onSelect: (path: string) => void }) {
  const { t } = useTranslation();
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [showBrowser, setShowBrowser] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pathInputRef = useRef<InputRef>(null);

  const handleConfirm = async (path: string) => {
    const trimmed = path.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    try {
      const res = await codingProjectApi.set(trimmed);
      onSelect(res.path);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : "Failed to open path";
      setError(detail);
      setLoading(false);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    // Debug: log all data transfer types
    console.debug("[ProjectSelectModal] drop types:", [...e.dataTransfer.types]);
    for (const t of e.dataTransfer.types) {
      console.debug(`[ProjectSelectModal]  ${t}:`, e.dataTransfer.getData(t));
    }

    // 1. macOS Finder drag: text/uri-list = "file:///path/to/folder\r\n"
    const uriList = e.dataTransfer.getData("text/uri-list");
    if (uriList?.trim()) {
      const firstUri = uriList.split(/\r?\n/).find((l) => l.startsWith("file://"));
      if (firstUri) {
        try {
          // Decode percent-encoding (%20 → space, etc.)
          const decoded = decodeURIComponent(firstUri.replace(/^file:\/\//, ""));
          setSelectedPath(decoded);
          return;
        } catch {
          // fall through
        }
      }
    }

    // 2. Text/plain drops (path strings dragged from terminal etc.)
    const text =
      e.dataTransfer.getData("text/plain") || e.dataTransfer.getData("text");
    if (text?.trim()) {
      setSelectedPath(text.trim());
      return;
    }

    // 3. Electron / desktop wrapper may expose File.path
    const file = e.dataTransfer.files[0];
    if (file) {
      const filePath = (file as File & { path?: string }).path;
      if (filePath) {
        setSelectedPath(filePath);
        return;
      }
      // Last fallback: put the folder name in the text input as a hint
      if (pathInputRef.current?.input) {
        pathInputRef.current.input.value = file.name;
        pathInputRef.current.focus();
      }
    }
  };

  const handleClearSelection = () => {
    setSelectedPath(null);
    setShowBrowser(false);
    setError(null);
  };

  return (
    <div className={styles.tabContent}>
      {selectedPath ? (
        /* ── Selected state (like plugin selectionCard) ─────────────── */
        <>
          <div className={styles.selectionCard}>
            <FolderOpen size={18} />
            <span className={styles.selectionName}>{selectedPath.split("/").pop() || selectedPath}</span>
            <span className={styles.selectionPath}>{selectedPath}</span>
            <button type="button" className={styles.clearBtn} onClick={handleClearSelection}>
              <X size={14} />
            </button>
          </div>
          {error && <Alert type="error" message={error} className={styles.alert} showIcon />}
          <Button
            type="primary"
            onClick={() => void handleConfirm(selectedPath)}
            loading={loading}
            className={styles.actionBtn}
          >
            {t("codingMode.openBtn")}
          </Button>
        </>
      ) : showBrowser ? (
        /* ── Server-side directory browser ──────────────────────────── */
        <>
          <FolderPicker
            onSelect={(p) => { setSelectedPath(p); setShowBrowser(false); }}
          />
          <button type="button" className={styles.backLink} onClick={() => setShowBrowser(false)}>
            ← Back
          </button>
        </>
      ) : (
        /* ── Drop zone (like plugin import) ─────────────────────────── */
        <>
          <div
            className={`${styles.dropZone} ${dragOver ? styles.dropZoneActive : ""}`}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => setShowBrowser(true)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && setShowBrowser(true)}
          >
            <FolderOpen size={36} strokeWidth={1.2} className={styles.dropFolderIcon} />
            <span className={styles.dropPrimary}>
              Drag a folder here, or click to browse
            </span>
            <span className={styles.dropSecondary}>
              You can also drag a path string from your terminal
            </span>
          </div>

          {/* Manual paste as fallback */}
          <div className={styles.orDivider}>— or paste a path —</div>
          <Input
            ref={pathInputRef}
            placeholder={t("codingMode.localPathPlaceholder")}
            className={styles.input}
            allowClear
            onPressEnter={(e) => {
              const val = ((e.target) as HTMLInputElement).value.trim();
              if (val) setSelectedPath(val);
            }}
            suffix={
              <button
                type="button"
                className={styles.pasteConfirmBtn}
                onClick={() => {
                  const val = pathInputRef.current?.input?.value.trim();
                  if (val) setSelectedPath(val);
                }}
              >
                Open
              </button>
            }
          />
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: New Project
// ---------------------------------------------------------------------------

function NewProjectTab({ onDone }: { onDone: (path: string) => void }) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await codingProjectApi.create(name.trim());
      onDone(res.path);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : "Failed to create project";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.tabContent}>
      <label className={styles.fieldLabel}>{t("codingMode.newName")}</label>
      <Input
        placeholder={t("codingMode.newNamePlaceholder")}
        value={name}
        onChange={(e) => setName(e.target.value)}
        className={styles.input}
      />
      {error && <Alert type="error" message={error} className={styles.alert} showIcon />}
      <Button
        type="primary"
        onClick={() => void handleCreate()}
        loading={loading}
        disabled={!name.trim()}
        className={styles.actionBtn}
      >
        {t("codingMode.createBtn")}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recent Projects list (shown below tabs)
// ---------------------------------------------------------------------------

function RecentProjects({
  projects,
  onSelect,
}: {
  projects: ProjectListItem[];
  onSelect: (path: string) => void;
}) {
  if (projects.length === 0) return null;
  return (
    <div className={styles.recentWrap}>
      <div className={styles.recentTitle}>Recent</div>
      <List
        size="small"
        dataSource={projects}
        renderItem={(item) => (
          <List.Item
            className={`${styles.recentItem} ${item.is_active ? styles.recentItemActive : ""}`}
            onClick={() => onSelect(item.path)}
          >
            <GitBranch size={13} className={styles.recentIcon} />
            <span className={styles.recentName}>{item.name}</span>
            <span className={styles.recentPath}>{item.path}</span>
          </List.Item>
        )}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Modal
// ---------------------------------------------------------------------------

export default function ProjectSelectModal({
  open,
  onClose,
  onConfirm,
}: ProjectSelectModalProps) {
  const { t } = useTranslation();
  const { projectDir, setProjectDir } = useProjectDir();
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [activeTab, setActiveTab] = useState("workspace");

  // Load recent projects when modal opens
  const loadProjects = async () => {
    try {
      const list = await codingProjectApi.list();
      setProjects(list);
    } catch {
      // ignore
    }
  };

  const handleOpen = () => {
    void loadProjects();
  };

  const handleConfirm = async (path: string | null) => {
    if (path !== undefined) {
      // path was set via API call already (Local / Create),
      // or explicitly null (workspace default).
      setProjectDir(path);
      onConfirm(path);
    }
  };

  const handlePathSelected = (path: string | null) => {
    setProjectDir(path);
    onConfirm(path);
  };

  const handleCloneDone = async (path: string) => {
    // After clone, the server already set the active project; update store.
    setProjectDir(path);
    onConfirm(path);
  };

  const handleLocalDone = (path: string) => {
    setProjectDir(path);
    onConfirm(path);
  };

  const handleNewDone = (path: string) => {
    setProjectDir(path);
    onConfirm(path);
  };

  const tabItems = [
    {
      key: "workspace",
      label: (
        <span className={styles.tabLabel}>
          <HardDrive size={13} />
          {t("codingMode.tabWorkspace")}
        </span>
      ),
      children: (
        <WorkspaceTab
          currentProjectDir={projectDir}
          onSelect={() => void handleConfirm(null)}
        />
      ),
    },
    {
      key: "clone",
      label: (
        <span className={styles.tabLabel}>
          <GitBranch size={13} />
          {t("codingMode.tabClone")}
        </span>
      ),
      children: <CloneTab onDone={(p) => void handleCloneDone(p)} />,
    },
    {
      key: "local",
      label: (
        <span className={styles.tabLabel}>
          <FolderOpen size={13} />
          {t("codingMode.tabLocal")}
        </span>
      ),
      children: <LocalPathTab onSelect={handleLocalDone} />,
    },
    {
      key: "new",
      label: (
        <span className={styles.tabLabel}>
          <PlusCircle size={13} />
          {t("codingMode.tabNew")}
        </span>
      ),
      children: <NewProjectTab onDone={handleNewDone} />,
    },
  ];

  return (
    <Modal
      open={open}
      title={t("codingMode.selectProject")}
      onCancel={onClose}
      footer={null}
      width={560}
      afterOpenChange={(isOpen) => isOpen && handleOpen()}
      className={styles.modal}
    >
      <p className={styles.desc}>{t("codingMode.selectProjectDesc")}</p>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="small"
      />
      <RecentProjects projects={projects} onSelect={handlePathSelected} />
    </Modal>
  );
}
