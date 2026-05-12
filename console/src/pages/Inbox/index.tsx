import { useEffect, useMemo, useRef, useState } from "react";
import {
  Tabs,
  Empty,
  Button,
  Badge,
  Collapse,
  Pagination,
  Checkbox,
  Popconfirm,
  message,
  Modal,
  Descriptions,
  Tag,
  Spin,
  Select,
} from "antd";
import {
  BulbOutlined,
  CopyOutlined,
  DownOutlined,
  ToolOutlined,
} from "@ant-design/icons";
import { PackageOpen, Bell } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { ApprovalCard as GlobalApprovalCard } from "../../components/ApprovalCard/ApprovalCard";
import { useApprovalContext } from "../../contexts/ApprovalContext";
import api from "../../api";
import { commandsApi } from "../../api/modules/commands";
import { chatApi } from "../../api/modules/chat";
import sessionApi from "../Chat/sessionApi";
import { PushMessageCard } from "./components";
import { useInboxData } from "./hooks/useInboxData";
import type { PushMessage } from "./types";
import { useAgentStore } from "../../stores/agentStore";
import {
  DEFAULT_AGENT_ID,
  getAgentDisplayName,
} from "../../utils/agentDisplayName";
import styles from "./index.module.less";

type TabKey = "approvals" | "messages";
const INBOX_TAB_STORAGE_KEY = "qwenpaw.inbox.activeTab";
const PUSH_MESSAGES_PAGE_SIZE = 5;

const resolveInitialTab = (): TabKey => {
  if (typeof window === "undefined") {
    return "messages";
  }
  const stored = window.localStorage.getItem(INBOX_TAB_STORAGE_KEY);
  if (stored === "approvals" || stored === "messages") {
    return stored;
  }
  return "messages";
};

const buildContentFallbackTrace = (messageItem: PushMessage) => ({
  events: messageItem.content
    ? [
        {
          at: messageItem.createdAt.getTime() / 1000,
          event: {
            role: "assistant",
            name: "assistant",
            content: [
              {
                type: "text",
                text: messageItem.content,
              },
            ],
          },
        },
      ]
    : [],
});

const getPrimaryTraceBlock = (
  event: Record<string, unknown>,
): Record<string, unknown> | null => {
  const content = event.content;
  if (!Array.isArray(content) || !content.length) return null;
  const first = content[0];
  if (!first || typeof first !== "object") return null;
  return first as Record<string, unknown>;
};

const isCollapsibleTraceEvent = (
  kind: string,
  event: Record<string, unknown>,
): boolean => {
  const lowerKind = kind.toLowerCase();
  if (lowerKind.includes("thinking") || lowerKind.includes("tool")) {
    return true;
  }
  const block = getPrimaryTraceBlock(event);
  const blockType = String(block?.type || "").toLowerCase();
  if (
    blockType === "thinking" ||
    blockType === "tool_use" ||
    blockType === "tool_result"
  ) {
    return true;
  }
  return false;
};

const extractTraceText = (event: Record<string, unknown>): string => {
  const block = getPrimaryTraceBlock(event);
  if (!block) return "";
  const blockType = String(block.type || "").toLowerCase();
  if (blockType === "thinking") {
    const thinking = block.thinking;
    if (typeof thinking === "string" && thinking.trim()) {
      return thinking.trim();
    }
  }
  if (blockType === "text") {
    const text = block.text;
    if (typeof text === "string" && text.trim()) {
      return text.trim();
    }
  }
  if (blockType === "tool_result") {
    const output = block.output;
    if (Array.isArray(output)) {
      const textChunks = output
        .map((item) => {
          if (!item || typeof item !== "object") return "";
          const text = (item as Record<string, unknown>).text;
          return typeof text === "string" ? text : "";
        })
        .filter(Boolean);
      if (textChunks.length) return textChunks.join("\n");
    }
  }
  if (blockType === "tool_use") {
    const rawInput = block.raw_input;
    if (typeof rawInput === "string" && rawInput.trim()) {
      return rawInput.trim();
    }
  }
  return "";
};

const normalizeTraceKind = (event: Record<string, unknown>): string => {
  if (event.type === "response_completed") return "response_completed";
  const block = getPrimaryTraceBlock(event);
  const blockType = String(block?.type || "").toLowerCase();
  if (blockType === "thinking") return "thinking";
  if (blockType === "tool_use") return "tool_call";
  if (blockType === "tool_result") return "tool_output";
  if (blockType === "text") return "push_preview";
  return "event";
};

type TraceDisplayItem = {
  at: number;
  eventType: string;
  eventRecord: Record<string, unknown>;
  traceText: string;
  collapsible: boolean;
  collapseTitle: string;
  toolInput?: string;
  toolOutput?: string;
  renderKind: "tool_pair" | "normal";
};

const shouldHideTraceEvent = (
  eventType: string,
  eventRecord: Record<string, unknown>,
): boolean => {
  const lowerType = eventType.toLowerCase();
  if (lowerType === "response_completed") return true;
  if (
    !extractTraceText(eventRecord) &&
    !isCollapsibleTraceEvent(eventType, eventRecord)
  ) {
    return true;
  }
  return false;
};

const getTraceFoldTitle = (
  eventType: string,
  eventRecord: Record<string, unknown>,
): string => {
  const lowerType = eventType.toLowerCase();
  if (lowerType.includes("thinking")) return "Thinking";
  if (lowerType.includes("tool")) {
    const block = getPrimaryTraceBlock(eventRecord);
    const toolName = block?.name;
    if (typeof toolName === "string" && toolName.trim()) {
      return toolName;
    }
    return "Tool";
  }
  return "Details";
};

const getTraceFoldIcon = (eventType: string) => {
  const lowerType = eventType.toLowerCase();
  if (lowerType.includes("thinking")) {
    return <BulbOutlined />;
  }
  if (lowerType.includes("tool")) {
    return <ToolOutlined />;
  }
  return null;
};

const getToolFieldText = (
  eventRecord: Record<string, unknown>,
  field: "tool_input" | "tool_output",
): string => {
  const block = getPrimaryTraceBlock(eventRecord);
  if (!block) return "";
  const blockType = String(block.type || "").toLowerCase();
  if (field === "tool_input" && blockType === "tool_use") {
    const rawInput = block.raw_input;
    if (typeof rawInput === "string" && rawInput.trim()) return rawInput;
    const input = block.input;
    if (input !== undefined) {
      try {
        return JSON.stringify(input, null, 2);
      } catch {
        return String(input);
      }
    }
  }
  if (field === "tool_output" && blockType === "tool_result") {
    const output = block.output;
    if (output !== undefined) {
      try {
        return JSON.stringify(output, null, 2);
      } catch {
        return String(output);
      }
    }
  }
  return "";
};

const formatToolInput = (text: string): string => {
  if (!text.trim()) return "{}";
  return text;
};

const formatToolBlockContent = (text: string): string => {
  const normalized = text.trim();
  if (!normalized) return "";
  try {
    const parsed = JSON.parse(normalized);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return text;
  }
};

const normalizeDetailTaskName = (title: string): string => {
  if (!title) return "-";
  return title
    .replace(/^(cron result|heartbeat result)\s*[:：]\s*/i, "")
    .replace(/^(定时任务结果|心跳结果)\s*[:：]\s*/i, "")
    .trim();
};

const getDetailModalTitle = (
  messageItem: PushMessage | null,
  t: (key: string, options?: Record<string, unknown>) => string,
): string => {
  if (!messageItem) return t("inbox.messageDetailTitle");
  const sourceType = (messageItem.metadata?.sourceType || "").toLowerCase();
  if (sourceType === "cron") {
    return t("inbox.detailCronTitle", {
      name: normalizeDetailTaskName(messageItem.title),
    });
  }
  if (sourceType === "heartbeat") {
    return t("inbox.detailHeartbeatTitle");
  }
  return messageItem.title || t("inbox.messageDetailTitle");
};

const renderMarkdownText = (text: string, className: string) => (
  <div className={className}>
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
  </div>
);

export default function InboxPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabKey>(resolveInitialTab);
  const [markAllReading, setMarkAllReading] = useState(false);
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<
    string | undefined
  >(undefined);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<PushMessage | null>(
    null,
  );
  const [traceLoading, setTraceLoading] = useState(false);
  const [traceData, setTraceData] = useState<{
    events: Array<{ at: number; event: Record<string, unknown> }>;
  } | null>(null);
  const [expandedTraceMap, setExpandedTraceMap] = useState<
    Record<string, boolean>
  >({});
  const [messagesPage, setMessagesPage] = useState(1);
  const [selectedMessageIds, setSelectedMessageIds] = useState<string[]>([]);
  const traceContainerRef = useRef<HTMLDivElement | null>(null);
  const traceScrollTopByMessageRef = useRef<Record<string, number>>({});
  const agents = useAgentStore((state) => state.agents);
  const { approvals: pendingApprovals, setApprovals } = useApprovalContext();
  const {
    summary,
    pushMessages,
    markMessageAsRead,
    markAllMessagesAsRead,
    deleteMessage,
    deleteMessages,
  } = useInboxData();
  const agentDisplayNameById = useMemo(
    () =>
      new Map(agents.map((agent) => [agent.id, getAgentDisplayName(agent, t)])),
    [agents, t],
  );
  const filteredPushMessages = useMemo(() => {
    if (!selectedAgentFilter) {
      return pushMessages;
    }
    return pushMessages.filter(
      (message) =>
        (message.metadata?.agentId || DEFAULT_AGENT_ID) === selectedAgentFilter,
    );
  }, [pushMessages, selectedAgentFilter]);
  const pushMessageAgentOptions = useMemo(() => {
    const ids = new Set<string>(
      filteredPushMessages.map(
        (message) => message.metadata?.agentId || DEFAULT_AGENT_ID,
      ),
    );
    pushMessages.forEach((message) => {
      ids.add(message.metadata?.agentId || DEFAULT_AGENT_ID);
    });
    const options = Array.from(ids)
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b))
      .map((id) => ({
        value: id,
        label:
          agentDisplayNameById.get(id) ||
          (id === DEFAULT_AGENT_ID ? t("agent.defaultDisplayName") : id),
      }));
    return options;
  }, [agentDisplayNameById, filteredPushMessages, pushMessages, t]);
  const urgentApprovalCount = useMemo(
    () =>
      pendingApprovals.filter((item) =>
        ["high", "critical"].includes(item.severity?.toLowerCase?.() || ""),
      ).length,
    [pendingApprovals],
  );
  const pagedPushMessages = useMemo(() => {
    const start = (messagesPage - 1) * PUSH_MESSAGES_PAGE_SIZE;
    return filteredPushMessages.slice(start, start + PUSH_MESSAGES_PAGE_SIZE);
  }, [filteredPushMessages, messagesPage]);
  const currentPageMessageIds = useMemo(
    () => pagedPushMessages.map((item) => item.id),
    [pagedPushMessages],
  );
  const allCurrentPageSelected = useMemo(
    () =>
      currentPageMessageIds.length > 0 &&
      currentPageMessageIds.every((id) => selectedMessageIds.includes(id)),
    [currentPageMessageIds, selectedMessageIds],
  );
  const totalMessagePages = Math.max(
    1,
    Math.ceil(filteredPushMessages.length / PUSH_MESSAGES_PAGE_SIZE),
  );

  const handleApproveRequest = async (
    requestId: string,
    rootSessionId: string,
  ) => {
    await commandsApi.sendApprovalCommand("approve", requestId, rootSessionId);
    setApprovals((prev) =>
      prev.filter((item) => item.request_id !== requestId),
    );
    message.success(t("approval.approved"));
  };

  const handleRejectRequest = async (
    requestId: string,
    rootSessionId: string,
  ) => {
    await commandsApi.sendApprovalCommand("deny", requestId, rootSessionId);
    setApprovals((prev) =>
      prev.filter((item) => item.request_id !== requestId),
    );
    message.success(t("approval.denied"));
  };

  const handleCancelTask = async (rootSessionId: string) => {
    const resolvedChatId =
      sessionApi.getRealIdForSession(rootSessionId) ?? rootSessionId;
    await chatApi.stopChat(resolvedChatId);
    setApprovals((prev) =>
      prev.filter((item) => item.root_session_id !== rootSessionId),
    );
  };
  const traceEvents = useMemo<TraceDisplayItem[]>(() => {
    if (!traceData) return [];
    const normalized = traceData.events
      .flatMap((item) => {
        const eventRecord = (item.event || {}) as Record<string, unknown>;
        const content = eventRecord.content;
        if (Array.isArray(content) && content.length > 1) {
          return content.map((block) => {
            const blockRecord = {
              ...eventRecord,
              content: [block],
            } as Record<string, unknown>;
            return {
              ...item,
              eventRecord: blockRecord,
              eventType: normalizeTraceKind(blockRecord),
            };
          });
        }
        const normalizedRecord =
          Array.isArray(content) && content.length === 1
            ? eventRecord
            : ({ ...eventRecord } as Record<string, unknown>);
        return [
          {
            ...item,
            eventRecord: normalizedRecord,
            eventType: normalizeTraceKind(normalizedRecord),
          },
        ];
      })
      .filter(
        (item) => !shouldHideTraceEvent(item.eventType, item.eventRecord),
      );
    const grouped: TraceDisplayItem[] = [];
    for (let i = 0; i < normalized.length; i += 1) {
      const current = normalized[i];
      const traceText = extractTraceText(current.eventRecord);
      const collapsible = isCollapsibleTraceEvent(
        current.eventType,
        current.eventRecord,
      );
      const collapseTitle = getTraceFoldTitle(
        current.eventType,
        current.eventRecord,
      );

      if (current.eventType === "tool_call") {
        const next = normalized[i + 1];
        const currentToolName = String(current.eventRecord.tool_name || "");
        const nextToolName = String(next?.eventRecord?.tool_name || "");
        const canPair =
          !!next &&
          next.eventType === "tool_output" &&
          (!!currentToolName || !!nextToolName)
            ? currentToolName === nextToolName
            : true;
        const toolInput = getToolFieldText(current.eventRecord, "tool_input");
        if (canPair && next) {
          const nextTraceText = extractTraceText(next.eventRecord);
          const toolOutput =
            getToolFieldText(next.eventRecord, "tool_output") || nextTraceText;
          grouped.push({
            at: current.at,
            eventType: "tool_call",
            eventRecord: current.eventRecord,
            traceText,
            collapsible: true,
            collapseTitle:
              collapseTitle ||
              getTraceFoldTitle(next.eventType, next.eventRecord),
            toolInput,
            toolOutput,
            renderKind: "tool_pair",
          });
          i += 1;
          continue;
        }
        grouped.push({
          at: current.at,
          eventType: current.eventType,
          eventRecord: current.eventRecord,
          traceText,
          collapsible: true,
          collapseTitle,
          toolInput,
          renderKind: "tool_pair",
        });
        continue;
      }

      if (current.eventType === "tool_output") {
        const toolOutput =
          getToolFieldText(current.eventRecord, "tool_output") || traceText;
        grouped.push({
          at: current.at,
          eventType: current.eventType,
          eventRecord: current.eventRecord,
          traceText,
          collapsible: true,
          collapseTitle,
          toolOutput,
          renderKind: "tool_pair",
        });
        continue;
      }

      grouped.push({
        at: current.at,
        eventType: current.eventType,
        eventRecord: current.eventRecord,
        traceText,
        collapsible,
        collapseTitle,
        renderKind: "normal",
      });
    }
    return grouped;
  }, [traceData]);

  const copyTraceBlock = async (text: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      message.success(t("common.copied"));
    } catch {
      message.error(t("common.copyFailed"));
    }
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(INBOX_TAB_STORAGE_KEY, activeTab);
    }
  }, [activeTab]);

  useEffect(() => {
    if (messagesPage > totalMessagePages) {
      setMessagesPage(totalMessagePages);
    }
  }, [messagesPage, totalMessagePages]);

  useEffect(() => {
    const validIdSet = new Set(pushMessages.map((item) => item.id));
    setSelectedMessageIds((prev) => prev.filter((id) => validIdSet.has(id)));
  }, [pushMessages]);
  useEffect(() => {
    setMessagesPage(1);
  }, [selectedAgentFilter]);

  useEffect(() => {
    setExpandedTraceMap({});
  }, [traceData, detailOpen]);

  useEffect(() => {
    if (
      !detailOpen ||
      traceLoading ||
      traceEvents.length <= 0 ||
      !selectedMessage
    ) {
      return;
    }
    const messageId = selectedMessage.id;
    const savedScrollTop = traceScrollTopByMessageRef.current[messageId];
    const rafId = window.requestAnimationFrame(() => {
      const container = traceContainerRef.current;
      if (!container) return;
      container.scrollTop =
        typeof savedScrollTop === "number"
          ? savedScrollTop
          : container.scrollHeight;
    });
    return () => window.cancelAnimationFrame(rafId);
  }, [detailOpen, selectedMessage, traceEvents.length, traceLoading]);

  const handleViewMessage = (messageId: string) => {
    const found = pushMessages.find((item) => item.id === messageId);
    if (!found) {
      message.warning(t("inbox.messageNotFound"));
      return;
    }
    if (!found.read) {
      markMessageAsRead(found.id);
    }
    setSelectedMessage(found.read ? found : { ...found, read: true });
    setDetailOpen(true);
    const runId =
      typeof found.metadata?.payload?.run_id === "string"
        ? (found.metadata.payload.run_id as string)
        : undefined;
    if (!runId) {
      setTraceData(buildContentFallbackTrace(found));
      return;
    }
    setTraceLoading(true);
    void api
      .getInboxTrace(runId)
      .then((trace) => {
        setTraceData({
          events: trace.events || [],
        });
      })
      .catch(() => {
        setTraceData(buildContentFallbackTrace(found));
      })
      .finally(() => setTraceLoading(false));
  };

  const handleMarkAllRead = async () => {
    if (summary.pushMessages.unread <= 0) {
      message.info(t("inbox.markAllReadNoUnread"));
      return;
    }
    setMarkAllReading(true);
    try {
      const updated = await markAllMessagesAsRead();
      message.success(t("inbox.markAllReadSuccess", { count: updated }));
    } catch {
      message.error(t("common.operationFailed"));
    } finally {
      setMarkAllReading(false);
    }
  };

  const handleToggleMessageSelection = (
    messageId: string,
    checked: boolean,
  ) => {
    setSelectedMessageIds((prev) => {
      if (checked) {
        if (prev.includes(messageId)) return prev;
        return [...prev, messageId];
      }
      return prev.filter((id) => id !== messageId);
    });
  };

  const handleToggleSelectCurrentPage = (checked: boolean) => {
    setSelectedMessageIds((prev) => {
      const pageSet = new Set(currentPageMessageIds);
      if (checked) {
        const merged = new Set(prev);
        currentPageMessageIds.forEach((id) => merged.add(id));
        return Array.from(merged);
      }
      return prev.filter((id) => !pageSet.has(id));
    });
  };

  const handleBatchDeleteMessages = async () => {
    if (!selectedMessageIds.length) return;
    const deletedCount = await deleteMessages(selectedMessageIds);
    setSelectedMessageIds([]);
    if (deletedCount > 0) {
      message.success(t("inbox.batchDeleteSuccess", { count: deletedCount }));
    }
  };

  const tabItems = [
    {
      key: "approvals",
      label: (
        <span className={styles.tabLabel}>
          <PackageOpen size={16} />
          {t("inbox.tabApprovals")}
          {urgentApprovalCount > 0 && <Badge count={urgentApprovalCount} />}
        </span>
      ),
      children: (
        <div className={styles.tabContent}>
          {pendingApprovals.length > 0 ? (
            <div className={styles.cardList}>
              {pendingApprovals.map((approval) => (
                <GlobalApprovalCard
                  key={approval.request_id}
                  requestId={approval.request_id}
                  agentId={approval.agent_id}
                  ownerAgentId={approval.owner_agent_id}
                  showInboxAgentContext
                  toolName={approval.tool_name}
                  severity={approval.severity}
                  findingsCount={approval.findings_count}
                  findingsSummary={approval.findings_summary}
                  toolParams={approval.tool_params}
                  createdAt={approval.created_at}
                  timeoutSeconds={approval.timeout_seconds}
                  sessionId={approval.session_id}
                  rootSessionId={approval.root_session_id}
                  onApprove={() =>
                    handleApproveRequest(
                      approval.request_id,
                      approval.root_session_id,
                    )
                  }
                  onDeny={() =>
                    handleRejectRequest(
                      approval.request_id,
                      approval.root_session_id,
                    )
                  }
                  onCancel={() => {
                    void handleCancelTask(approval.root_session_id);
                  }}
                  onAcknowledge={(requestId) => {
                    return commandsApi
                      .sendApprovalCommand(
                        "deny",
                        requestId,
                        approval.root_session_id,
                      )
                      .catch(() => undefined)
                      .then(() => {
                        setApprovals((prev) =>
                          prev.filter((item) => item.request_id !== requestId),
                        );
                      });
                  }}
                />
              ))}
            </div>
          ) : (
            <Empty description={t("inbox.emptyApprovals")} />
          )}
        </div>
      ),
    },
    {
      key: "messages",
      label: (
        <span className={styles.tabLabel}>
          <Bell size={16} />
          {t("inbox.tabPushMessages")}
          {summary.pushMessages.unread > 0 && (
            <Badge count={summary.pushMessages.unread} />
          )}
        </span>
      ),
      children: (
        <div className={styles.tabContent}>
          <div className={styles.messagesToolbar}>
            <div className={styles.messagesSelectionTools}>
              <Checkbox
                checked={allCurrentPageSelected}
                onChange={(event) =>
                  handleToggleSelectCurrentPage(event.target.checked)
                }
                disabled={currentPageMessageIds.length <= 0}
              >
                {t("inbox.selectAllCurrentPage")}
              </Checkbox>
              <span className={styles.selectedCountText}>
                {t("inbox.selectedItems", { count: selectedMessageIds.length })}
              </span>
              <Popconfirm
                title={t("inbox.batchDeleteConfirm", {
                  count: selectedMessageIds.length,
                })}
                onConfirm={() => void handleBatchDeleteMessages()}
                okText={t("common.confirm")}
                cancelText={t("common.cancel")}
                disabled={selectedMessageIds.length <= 0}
              >
                <Button danger disabled={selectedMessageIds.length <= 0}>
                  {t("inbox.batchDeleteButton")}
                </Button>
              </Popconfirm>
            </div>
            <div className={styles.messagesSelectionTools}>
              <Select
                size="small"
                value={selectedAgentFilter}
                onChange={(value) => setSelectedAgentFilter(value)}
                allowClear
                options={pushMessageAgentOptions}
                style={{ width: 180 }}
                placeholder={t("inbox.filterByAgent")}
              />
              <Button
                size="small"
                onClick={() => void handleMarkAllRead()}
                loading={markAllReading}
                disabled={summary.pushMessages.unread <= 0}
              >
                {t("inbox.markAllRead")}
              </Button>
            </div>
          </div>
          {filteredPushMessages.length > 0 ? (
            <div className={styles.cardList}>
              {pagedPushMessages.map((item) => (
                <PushMessageCard
                  key={item.id}
                  message={item}
                  onMarkAsRead={markMessageAsRead}
                  onDelete={deleteMessage}
                  onView={handleViewMessage}
                  selected={selectedMessageIds.includes(item.id)}
                  onSelectChange={handleToggleMessageSelection}
                />
              ))}
              <div className={styles.paginationWrap}>
                <Pagination
                  current={messagesPage}
                  total={filteredPushMessages.length}
                  pageSize={PUSH_MESSAGES_PAGE_SIZE}
                  onChange={setMessagesPage}
                  showSizeChanger={false}
                />
              </div>
            </div>
          ) : (
            <Empty description={t("inbox.emptyPush")} />
          )}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.inboxPage}>
      <PageHeader items={[{ title: t("inbox.title") }]} extra={null} />

      <div className={styles.pageContent}>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as TabKey)}
          items={tabItems}
          className={styles.inboxTabs}
        />
      </div>
      <Modal
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={820}
        title={getDetailModalTitle(selectedMessage, t)}
      >
        {selectedMessage ? (
          <div className={styles.messageDetail}>
            <Descriptions
              size="small"
              column={2}
              bordered
              className={styles.messageDetailMeta}
            >
              <Descriptions.Item label={t("inbox.detailStatus")}>
                <Tag
                  color={
                    selectedMessage.metadata?.status === "error"
                      ? "error"
                      : "success"
                  }
                >
                  {selectedMessage.metadata?.status || "success"}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t("inbox.detailAgent")}>
                {(() => {
                  const agentId =
                    selectedMessage.metadata?.agentId || DEFAULT_AGENT_ID;
                  return (
                    agentDisplayNameById.get(agentId) ||
                    (agentId === DEFAULT_AGENT_ID
                      ? t("agent.defaultDisplayName")
                      : agentId)
                  );
                })()}
              </Descriptions.Item>
              <Descriptions.Item label={t("inbox.detailReceivedAt")}>
                {selectedMessage.createdAt.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label={t("inbox.detailTaskId")}>
                {selectedMessage.id || "-"}
              </Descriptions.Item>
            </Descriptions>

            <div className={styles.messageDetailBlock}>
              <div className={styles.messageDetailLabel}>
                {t("inbox.detailExecutionTrace")}
              </div>
              {traceLoading ? (
                <div className={styles.traceLoading}>
                  <Spin size="small" />
                </div>
              ) : traceEvents.length > 0 ? (
                <div
                  ref={traceContainerRef}
                  className={styles.traceContainer}
                  onScroll={(event) => {
                    if (!selectedMessage) return;
                    traceScrollTopByMessageRef.current[selectedMessage.id] =
                      event.currentTarget.scrollTop;
                  }}
                >
                  <div className={styles.traceTimeline}>
                    {traceEvents.map((item, index) => {
                      const {
                        eventRecord,
                        eventType,
                        traceText,
                        collapsible,
                        collapseTitle,
                      } = item;
                      const kind = eventType;
                      const foldIcon = getTraceFoldIcon(kind);
                      const collapseKey = `trace-${item.at}-${index}`;
                      const isPanelActive = !!expandedTraceMap[collapseKey];
                      return (
                        <div
                          key={`${item.at}-${index}`}
                          className={styles.traceEntry}
                        >
                          {eventRecord.role === "user" && traceText ? (
                            <div className={styles.traceUserRow}>
                              <div className={styles.traceUserMessage}>
                                {traceText}
                              </div>
                            </div>
                          ) : kind === "push_preview" && traceText ? (
                            renderMarkdownText(
                              traceText,
                              `${styles.traceAssistantMessage} ${styles.traceStandaloneAligned}`,
                            )
                          ) : collapsible ? (
                            <Collapse
                              bordered={false}
                              ghost
                              activeKey={isPanelActive ? [collapseKey] : []}
                              onChange={(keys) => {
                                const nextActive = Array.isArray(keys)
                                  ? keys.length > 0
                                  : Boolean(keys);
                                setExpandedTraceMap((prev) => ({
                                  ...prev,
                                  [collapseKey]: nextActive,
                                }));
                              }}
                              className={`${styles.traceCollapse} ${
                                isPanelActive ? styles.traceCollapseActive : ""
                              }`}
                              expandIcon={() => null}
                              items={[
                                {
                                  key: collapseKey,
                                  label: (
                                    <div className={styles.traceFoldHeader}>
                                      {foldIcon ? (
                                        <span className={styles.traceFoldIcon}>
                                          {foldIcon}
                                        </span>
                                      ) : null}
                                      <span className={styles.traceFoldTitle}>
                                        {collapseTitle}
                                      </span>
                                      <span
                                        className={`${
                                          styles.traceInlineChevron
                                        } ${
                                          isPanelActive
                                            ? styles.traceInlineChevronActive
                                            : ""
                                        }`}
                                      >
                                        <DownOutlined />
                                      </span>
                                    </div>
                                  ),
                                  children:
                                    item.renderKind === "tool_pair" ? (
                                      <div className={styles.toolDetailWrap}>
                                        {item.toolInput ? (
                                          <div className={styles.toolSection}>
                                            <div
                                              className={styles.traceCodeHeader}
                                            >
                                              <div
                                                className={
                                                  styles.traceCodeTitle
                                                }
                                              >
                                                Input
                                              </div>
                                              <button
                                                type="button"
                                                className={
                                                  styles.traceCodeCopyBtn
                                                }
                                                onClick={() =>
                                                  void copyTraceBlock(
                                                    formatToolBlockContent(
                                                      formatToolInput(
                                                        item.toolInput || "",
                                                      ),
                                                    ),
                                                  )
                                                }
                                                title={t("common.copy")}
                                              >
                                                <CopyOutlined />
                                              </button>
                                            </div>
                                            <pre
                                              className={styles.toolCodeBlock}
                                            >
                                              {formatToolBlockContent(
                                                formatToolInput(item.toolInput),
                                              )}
                                            </pre>
                                          </div>
                                        ) : null}
                                        {item.toolOutput ? (
                                          <div className={styles.toolSection}>
                                            <div
                                              className={styles.traceCodeHeader}
                                            >
                                              <div
                                                className={
                                                  styles.traceCodeTitle
                                                }
                                              >
                                                Output
                                              </div>
                                              <button
                                                type="button"
                                                className={
                                                  styles.traceCodeCopyBtn
                                                }
                                                onClick={() =>
                                                  void copyTraceBlock(
                                                    formatToolBlockContent(
                                                      item.toolOutput || "",
                                                    ),
                                                  )
                                                }
                                                title={t("common.copy")}
                                              >
                                                <CopyOutlined />
                                              </button>
                                            </div>
                                            <pre
                                              className={styles.toolCodeBlock}
                                            >
                                              {formatToolBlockContent(
                                                item.toolOutput,
                                              )}
                                            </pre>
                                          </div>
                                        ) : null}
                                      </div>
                                    ) : traceText ? (
                                      renderMarkdownText(
                                        traceText,
                                        styles.traceMarkdownBlock,
                                      )
                                    ) : (
                                      <pre className={styles.traceJsonBlock}>
                                        {JSON.stringify(eventRecord, null, 2)}
                                      </pre>
                                    ),
                                },
                              ]}
                            />
                          ) : traceText ? (
                            renderMarkdownText(
                              traceText,
                              `${styles.traceMarkdownBlock} ${styles.traceStandaloneAligned}`,
                            )
                          ) : (
                            <pre
                              className={`${styles.traceJsonBlock} ${styles.traceStandaloneAligned}`}
                            >
                              {JSON.stringify(eventRecord, null, 2)}
                            </pre>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className={styles.traceEmpty}>
                  {t("inbox.detailTraceEmpty")}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
