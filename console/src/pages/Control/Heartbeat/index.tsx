import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Form,
  Input,
  message,
  Select,
  Switch,
} from "@agentscope-ai/design";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import type { HeartbeatConfig } from "../../../api/types/heartbeat";
import styles from "./index.module.less";

const TARGET_OPTIONS = [
  { value: "main", labelKey: "heartbeat.targetMain" },
  { value: "last", labelKey: "heartbeat.targetLast" },
];

function HeartbeatPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm<HeartbeatConfig & { useActiveHours?: boolean }>();

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const data = await api.getHeartbeatConfig();
      form.setFieldsValue({
        enabled: data.enabled ?? false,
        every: data.every ?? "6h",
        target: data.target ?? "main",
        useActiveHours: !!data.activeHours,
        activeHoursStart: data.activeHours?.start ?? "08:00",
        activeHoursEnd: data.activeHours?.end ?? "22:00",
      });
    } catch (e) {
      console.error("Failed to load heartbeat config:", e);
      message.error(t("heartbeat.loadFailed"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const onFinish = async (values: HeartbeatConfig & {
    useActiveHours?: boolean;
    activeHoursStart?: string;
    activeHoursEnd?: string;
  }) => {
    const body: HeartbeatConfig = {
      enabled: values.enabled ?? false,
      every: values.every ?? "6h",
      target: values.target ?? "main",
      activeHours: values.useActiveHours && values.activeHoursStart && values.activeHoursEnd
        ? { start: values.activeHoursStart, end: values.activeHoursEnd }
        : undefined,
    };
    setSaving(true);
    try {
      await api.updateHeartbeatConfig(body);
      message.success(t("heartbeat.saveSuccess"));
    } catch (e) {
      console.error("Failed to save heartbeat config:", e);
      message.error(t("heartbeat.saveFailed"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.heartbeatPage}>
        <h1 className={styles.title}>{t("heartbeat.title")}</h1>
        <p className={styles.description}>{t("heartbeat.description")}</p>
        <span className={styles.description}>{t("common.loading")}</span>
      </div>
    );
  }

  return (
    <div className={styles.heartbeatPage}>
      <h1 className={styles.title}>{t("heartbeat.title")}</h1>
      <p className={styles.description}>{t("heartbeat.description")}</p>

      <Card className={styles.card}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            enabled: false,
            every: "6h",
            target: "main",
            useActiveHours: false,
            activeHoursStart: "08:00",
            activeHoursEnd: "22:00",
          }}
        >
          <Form.Item
            name="enabled"
            label={t("heartbeat.enabled")}
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="every"
            label={t("heartbeat.every")}
            rules={[{ required: true, message: t("heartbeat.everyRequired") }]}
          >
            <Input placeholder="30m, 1h, 2h30m" />
          </Form.Item>

          <Form.Item
            name="target"
            label={t("heartbeat.target")}
            rules={[{ required: true }]}
          >
            <Select
              options={TARGET_OPTIONS.map((opt) => ({
                value: opt.value,
                label: t(opt.labelKey),
              }))}
            />
          </Form.Item>

          <Form.Item
            name="useActiveHours"
            label={t("heartbeat.activeHours")}
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.useActiveHours !== cur.useActiveHours}
          >
            {({ getFieldValue }) =>
              getFieldValue("useActiveHours") ? (
                <div className={styles.activeHoursRow}>
                  <Form.Item
                    name="activeHoursStart"
                    label={t("heartbeat.activeStart")}
                  >
                    <Input placeholder="08:00" />
                  </Form.Item>
                  <Form.Item
                    name="activeHoursEnd"
                    label={t("heartbeat.activeEnd")}
                  >
                    <Input placeholder="22:00" />
                  </Form.Item>
                </div>
              ) : null
            }
          </Form.Item>

          <Form.Item className={styles.formActions}>
            <Button type="primary" htmlType="submit" loading={saving}>
              {t("common.save")}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

export default HeartbeatPage;
