import {
  Drawer,
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  Button,
  message,
} from "@agentscope-ai/design";
import { Space } from "antd";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import type { FormInstance } from "antd";
import type { CronJobSpecOutput } from "../../../../api/types";
import { TIMEZONE_OPTIONS, DEFAULT_FORM_VALUES } from "./constants";
import { cronJobApi } from "../../../../api/modules/cronjob";

type CronJob = CronJobSpecOutput;

interface JobDrawerProps {
  open: boolean;
  editingJob: CronJob | null;
  form: FormInstance<CronJob>;
  onClose: () => void;
  onSubmit: (values: CronJob) => void;
}

export function JobDrawer({
  open,
  editingJob,
  form,
  onClose,
  onSubmit,
}: JobDrawerProps) {
  const { t } = useTranslation();
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [converting, setConverting] = useState(false);
  const [cronDescription, setCronDescription] = useState("");

  const handleConvert = async () => {
    if (!naturalLanguage.trim()) {
      message.warning("Please enter a natural language description");
      return;
    }

    setConverting(true);
    try {
      const result = await cronJobApi.parseCron(naturalLanguage);
      const input = naturalLanguage.trim();

      // Detect language
      const isChinese = /[\u4e00-\u9fff]/.test(input);

      // Extract task description: remove time-related words
      let taskDesc: string;
      if (isChinese) {
        // Chinese patterns
        taskDesc = input
          .replace(/每天|每周[一二三四五六日天]?|每月\d+号?|每小时|每\d+[分小]钟?时?/g, "")
          .replace(/[上下]午|早上|晚上|凌晨/g, "")
          .replace(/[零一二三四五六七八九十]+点|\d+点/g, "")
          .replace(/定时|提醒我?|自动/g, "")
          .trim() || input;
      } else {
        // English patterns
        taskDesc = input
          .replace(/every\s+(day|hour|minute|morning|afternoon|evening|night)|daily|hourly/gi, "")
          .replace(/every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)/gi, "")
          .replace(/weekdays?|weekends?/gi, "")
          .replace(/at\s+\d+\s*(am|pm)?/gi, "")
          .replace(/on\s+the\s+\d+(st|nd|rd|th)?\s+of\s+every\s+month/gi, "")
          .replace(/every\s+\d+\s+(hours?|minutes?)/gi, "")
          .replace(/\s+/g, " ")
          .trim() || input;
      }

      // Generate prompt for agent: keep the reminder context
      let agentPrompt: string;
      if (isChinese) {
        agentPrompt = input.includes("提醒") ? `提醒：${taskDesc}` : taskDesc;
      } else {
        agentPrompt = input.toLowerCase().includes("remind") ? `Reminder: ${taskDesc}` : taskDesc;
      }

      // Auto-generate ID
      const jobId = `job-${Date.now().toString(36)}`;

      // Fill all fields
      form.setFieldsValue({
        id: form.getFieldValue("id") || jobId,
        name: form.getFieldValue("name") || taskDesc,
        schedule: { cron: result.cron },
        task_type: form.getFieldValue("task_type") || "agent",
        enabled: true,
        text: form.getFieldValue("text") || taskDesc,
        request: {
          input: form.getFieldValue(["request", "input"]) ||
            JSON.stringify([{ role: "user", content: [{ text: agentPrompt, type: "text" }] }]),
        },
        dispatch: {
          channel: form.getFieldValue(["dispatch", "channel"]) || "console",
          target: {
            user_id: form.getFieldValue(["dispatch", "target", "user_id"]) || "admin",
            session_id: form.getFieldValue(["dispatch", "target", "session_id"]) || "default",
          },
        },
      });

      // Show description
      setCronDescription(result.description);

      // Show success message
      const sourceIcon = result.source === "rules" ? "⚡" : "🤖";
      message.success(`${sourceIcon} ${result.description}`);
    } catch (error) {
      message.error("Failed to parse. Please use standard cron format or clearer description");
      console.error("Failed to parse cron:", error);
    } finally {
      setConverting(false);
    }
  };

  const handleCronChange = () => {
    // Clear description when manually editing cron
    setCronDescription("");
  };

  return (
    <Drawer
      width={520}
      placement="right"
      title={editingJob ? t("cronJobs.editJob") : t("cronJobs.createJob")}
      open={open}
      onClose={onClose}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onSubmit}
        initialValues={DEFAULT_FORM_VALUES}
      >
        {/* Smart Input (Optional) */}
        <Form.Item label="🪄 Smart Input (Optional)">
          <Space.Compact style={{ width: "100%" }}>
            <Input
              placeholder="e.g., every day at 3pm remind me to run / 例如：每天下午3点提醒我跑步"
              value={naturalLanguage}
              onChange={(e) => setNaturalLanguage(e.target.value)}
              onPressEnter={handleConvert}
            />
            <Button type="primary" loading={converting} onClick={handleConvert}>
              Generate
            </Button>
          </Space.Compact>
          <div style={{ marginTop: 4, fontSize: 12, color: "#999" }}>
            💡 Enter natural language (EN/中文), auto-fill all fields below
          </div>
        </Form.Item>

        <Form.Item
          name="id"
          label="ID"
          rules={[{ required: true, message: t("cronJobs.pleaseInputId") }]}
        >
          <Input placeholder={t("cronJobs.jobIdPlaceholder")} />
        </Form.Item>

        <Form.Item
          name="name"
          label="Name"
          rules={[{ required: true, message: t("cronJobs.pleaseInputName") }]}
        >
          <Input placeholder={t("cronJobs.jobNamePlaceholder")} />
        </Form.Item>

        <Form.Item name={["schedule", "type"]} label="ScheduleType" hidden>
          <Input disabled value="cron" />
        </Form.Item>

        <Form.Item
          name={["schedule", "cron"]}
          label="ScheduleCron"
          rules={[{ required: true, message: t("cronJobs.pleaseInputCron") }]}
        >
          <Input placeholder="0 2 * * *" onChange={handleCronChange} />
        </Form.Item>

        {cronDescription && (
          <div
            style={{
              marginTop: -16,
              marginBottom: 16,
              fontSize: 12,
              color: "#52c41a",
            }}
          >
            📝 {cronDescription}
          </div>
        )}

        <Form.Item name={["schedule", "timezone"]} label="ScheduleTimezone">
          <Select
            showSearch
            placeholder={t("cronJobs.selectTimezone")}
            filterOption={(input, option) =>
              (option?.label?.toString() || "")
                .toLowerCase()
                .includes(input.toLowerCase())
            }
            options={TIMEZONE_OPTIONS}
          />
        </Form.Item>

        <Form.Item
          name="task_type"
          label="TaskType"
          rules={[
            { required: true, message: t("cronJobs.pleaseSelectTaskType") },
          ]}
        >
          <Select>
            <Select.Option value="text">text</Select.Option>
            <Select.Option value="agent">agent</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item name="enabled" label="Enabled" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item name="text" label="Text">
          <Input.TextArea
            rows={3}
            placeholder={t("cronJobs.taskDescriptionPlaceholder")}
          />
        </Form.Item>

        <Form.Item
          name={["request", "input"]}
          label="RequestInput"
          rules={[
            { required: true, message: t("cronJobs.pleaseInputRequest") },
            {
              validator: (_, value) => {
                if (!value) return Promise.resolve();
                try {
                  JSON.parse(value);
                  return Promise.resolve();
                } catch {
                  return Promise.reject(
                    new Error(t("cronJobs.invalidJsonFormat")),
                  );
                }
              },
            },
          ]}
          tooltip={t("cronJobs.jsonFormatRequired")}
        >
          <Input.TextArea
            rows={6}
            placeholder='[{"role":"user","content":[{"text":"Hello","type":"text"}]}]'
            style={{ fontFamily: "monospace", fontSize: 12 }}
          />
        </Form.Item>

        <Form.Item name={["request", "session_id"]} label="RequestSessionId">
          <Input placeholder="default" />
        </Form.Item>

        <Form.Item name={["request", "user_id"]} label="RequestUserId">
          <Input placeholder="system" />
        </Form.Item>

        <Form.Item name={["dispatch", "type"]} label="DispatchType" hidden>
          <Input disabled value="channel" />
        </Form.Item>

        <Form.Item
          name={["dispatch", "channel"]}
          label="DispatchChannel"
          rules={[
            { required: true, message: t("cronJobs.pleaseInputChannel") },
          ]}
        >
          <Input placeholder="console" />
        </Form.Item>

        <Form.Item
          name={["dispatch", "target", "user_id"]}
          label="DispatchTargetUserId"
          rules={[{ required: true, message: t("cronJobs.pleaseInputUserId") }]}
        >
          <Input placeholder="admin" />
        </Form.Item>

        <Form.Item
          name={["dispatch", "target", "session_id"]}
          label="DispatchTargetSessionId"
          rules={[
            { required: true, message: t("cronJobs.pleaseInputSessionId") },
          ]}
        >
          <Input placeholder="default" />
        </Form.Item>

        <Form.Item name={["dispatch", "mode"]} label="DispatchMode">
          <Select>
            <Select.Option value="stream">stream</Select.Option>
            <Select.Option value="final">final</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name={["runtime", "max_concurrency"]}
          label="RuntimeMaxConcurrency"
        >
          <InputNumber min={1} style={{ width: "100%" }} />
        </Form.Item>

        <Form.Item
          name={["runtime", "timeout_seconds"]}
          label="RuntimeTimeoutSeconds"
        >
          <InputNumber min={1} style={{ width: "100%" }} />
        </Form.Item>

        <Form.Item
          name={["runtime", "misfire_grace_seconds"]}
          label="RuntimeMisfireGraceSeconds"
        >
          <InputNumber min={0} style={{ width: "100%" }} />
        </Form.Item>

        <Form.Item>
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: 8,
              marginTop: 16,
            }}
          >
            <Button onClick={onClose}>{t("common.cancel")}</Button>
            <Button type="primary" htmlType="submit">
              {t("common.save")}
            </Button>
          </div>
        </Form.Item>
      </Form>
    </Drawer>
  );
}
