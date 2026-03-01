import { useEffect, useRef, useState, useCallback } from "react";
import { Modal, Button, Tag, Typography, Space, List, message } from "antd";
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { api } from "../../api";
import type { ApprovalRequest } from "../../api/modules/approval";
import { getApiUrl } from "../../api/config";

const { Text, Paragraph } = Typography;

/** Human-readable labels for tool actions. */
const ACTION_LABELS: Record<string, string> = {
  execute_shell_command: "Shell Command",
  write_file: "Write File",
  edit_file: "Edit File",
  append_file: "Append File",
  browser_use: "Browser",
};

export default function ApprovalModal() {
  const { t } = useTranslation();
  const [pending, setPending] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const eventSourceRef = useRef<EventSource | null>(null);

  // Connect SSE for real-time approval events
  useEffect(() => {
    const url = getApiUrl("/approvals/stream/events");
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener("approval_request", (e: MessageEvent) => {
      try {
        const req: ApprovalRequest = JSON.parse(e.data);
        setPending((prev) => {
          if (prev.some((p) => p.id === req.id)) return prev;
          return [...prev, req];
        });
      } catch {
        // ignore parse errors
      }
    });

    es.onerror = () => {
      // Reconnect is automatic for EventSource; just log.
      console.warn("Approval SSE connection error, will retry…");
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, []);

  const handleApprove = useCallback(async (id: string) => {
    setLoading((prev) => ({ ...prev, [id]: true }));
    try {
      await api.approve(id);
      setPending((prev) => prev.filter((r) => r.id !== id));
    } catch {
      message.error("Failed to approve request");
    } finally {
      setLoading((prev) => ({ ...prev, [id]: false }));
    }
  }, []);

  const handleDeny = useCallback(async (id: string) => {
    setLoading((prev) => ({ ...prev, [id]: true }));
    try {
      await api.deny(id);
      setPending((prev) => prev.filter((r) => r.id !== id));
    } catch {
      message.error("Failed to deny request");
    } finally {
      setLoading((prev) => ({ ...prev, [id]: false }));
    }
  }, []);

  if (pending.length === 0) return null;

  return (
    <Modal
      title={
        <Space>
          <ExclamationCircleOutlined style={{ color: "#faad14" }} />
          {t("approval.title", "Approval Required")}
        </Space>
      }
      open={pending.length > 0}
      footer={null}
      closable={false}
      maskClosable={false}
      width={520}
    >
      <List
        dataSource={pending}
        renderItem={(req) => (
          <List.Item
            key={req.id}
            actions={[
              <Button
                key="approve"
                type="primary"
                icon={<CheckCircleOutlined />}
                loading={loading[req.id]}
                onClick={() => handleApprove(req.id)}
              >
                {t("approval.approve", "Approve")}
              </Button>,
              <Button
                key="deny"
                danger
                icon={<CloseCircleOutlined />}
                loading={loading[req.id]}
                onClick={() => handleDeny(req.id)}
              >
                {t("approval.deny", "Deny")}
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Tag color="orange">
                    {ACTION_LABELS[req.action] || req.action}
                  </Tag>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {req.id}
                  </Text>
                </Space>
              }
              description={
                <>
                  <Paragraph
                    style={{ marginBottom: 4 }}
                    ellipsis={{ rows: 2 }}
                  >
                    {req.summary || req.target}
                  </Paragraph>
                  {req.target && req.summary && (
                    <Text code style={{ fontSize: 12 }}>
                      {req.target.length > 80
                        ? req.target.slice(0, 80) + "…"
                        : req.target}
                    </Text>
                  )}
                </>
              }
            />
          </List.Item>
        )}
      />
    </Modal>
  );
}
