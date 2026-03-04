import { useState, useEffect, useMemo } from "react";
import { Form, Input, Modal, message, Button } from "@agentscope-ai/design";
import { ApiOutlined } from "@ant-design/icons";
import type { ProviderConfigRequest } from "../../../../../api/types";
import api from "../../../../../api";
import { useTranslation } from "react-i18next";
import styles from "../../index.module.less";

interface ProviderConfigModalProps {
  provider: {
    id: string;
    name: string;
    current_api_key?: string;
    api_key_prefix?: string;
    current_base_url?: string;
    is_custom: boolean;
    needs_base_url: boolean;
  };
  activeModels: any;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export function ProviderConfigModal({
  provider,
  activeModels,
  open,
  onClose,
  onSaved,
}: ProviderConfigModalProps) {
  const { t } = useTranslation();
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [formDirty, setFormDirty] = useState(false);
  const [form] = Form.useForm<ProviderConfigRequest>();
  const canEditBaseUrl = provider.needs_base_url || provider.id === "ollama";

  const apiKeyExtra = useMemo(() => {
    if (provider.current_api_key) {
      return t("models.currentKey", { key: provider.current_api_key });
    }
    if (provider.api_key_prefix) {
      return t("models.startsWith", { prefix: provider.api_key_prefix });
    }
    return t("models.optionalSelfHosted");
  }, [provider.current_api_key, provider.api_key_prefix, t]);

  const apiKeyPlaceholder = useMemo(() => {
    if (provider.current_api_key) {
      return t("models.leaveBlankKeep");
    }
    if (provider.api_key_prefix) {
      return t("models.enterApiKey", { prefix: provider.api_key_prefix });
    }
    return t("models.enterApiKeyOptional");
  }, [provider.current_api_key, provider.api_key_prefix, t]);

  // Sync form when modal opens or provider data changes
  useEffect(() => {
    if (open) {
      form.setFieldsValue({
        api_key: undefined,
        base_url: provider.current_base_url || undefined,
      });
      setFormDirty(false);
    }
  }, [provider, form, open]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      // Only include api_key in the payload when the user actually typed a new value.
      // Leaving the field blank means "keep existing key unchanged" — revoke is the only way to clear it.
      const newApiKey = values.api_key?.trim() || null;
      const hasNewApiKey = !!newApiKey;
      const normalizedBaseUrl = values.base_url?.trim() || null;

      const testPayload: { api_key?: string | null; base_url?: string | null } =
        { base_url: normalizedBaseUrl };
      if (hasNewApiKey) testPayload.api_key = newApiKey;

      const result = await api.testProviderConnection(provider.id, testPayload);

      if (!result.success) {
        message.error(result.message || t("models.testConnectionFailed"));
        return;
      }

      const savePayload: { api_key?: string | null; base_url?: string | null } =
        { base_url: normalizedBaseUrl };
      if (hasNewApiKey) savePayload.api_key = newApiKey;

      await api.configureProvider(provider.id, savePayload);
      await onSaved();
      setFormDirty(false);
      onClose();
      message.success(t("models.configurationSaved", { name: provider.name }));
    } catch (error) {
      if (error && typeof error === "object" && "errorFields" in error) return;
      const errMsg =
        error instanceof Error ? error.message : t("models.failedToSaveConfig");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const values = await form.validateFields();
      const newApiKey = values.api_key?.trim() || null;
      const testPayload: { api_key?: string | null; base_url?: string | null } =
        { base_url: values.base_url?.trim() || null };
      if (newApiKey) testPayload.api_key = newApiKey;
      const result = await api.testProviderConnection(provider.id, testPayload);
      if (result.success) {
        message.success(result.message || t("models.testConnectionSuccess"));
      } else {
        message.warning(result.message || t("models.testConnectionFailed"));
      }
    } catch (error) {
      if (error && typeof error === "object" && "errorFields" in error) return;
      const errMsg =
        error instanceof Error
          ? error.message
          : t("models.testConnectionError");
      message.error(errMsg);
    } finally {
      setTesting(false);
    }
  };

  const isActiveLlmProvider =
    activeModels?.active_llm?.provider_id === provider.id;

  const handleRevoke = () => {
    const confirmContent = isActiveLlmProvider
      ? t("models.revokeConfirmContent", { name: provider.name })
      : t("models.revokeConfirmSimple", { name: provider.name });

    Modal.confirm({
      title: t("models.revokeAuthorization"),
      content: confirmContent,
      okText: t("models.revokeAuthorization"),
      okButtonProps: { danger: true },
      cancelText: t("models.cancel"),
      onOk: async () => {
        try {
          await api.configureProvider(provider.id, { api_key: null });
          await onSaved();
          onClose();
          if (isActiveLlmProvider) {
            message.success(
              t("models.authorizationRevoked", { name: provider.name }),
            );
          } else {
            message.success(
              t("models.authorizationRevokedSimple", { name: provider.name }),
            );
          }
        } catch (error) {
          const errMsg =
            error instanceof Error ? error.message : t("models.failedToRevoke");
          message.error(errMsg);
        }
      },
    });
  };

  return (
    <Modal
      title={t("models.configureProvider", { name: provider.name })}
      open={open}
      onCancel={onClose}
      footer={
        <div className={styles.modalFooter}>
          <div className={styles.modalFooterLeft}>
            {provider.current_api_key && (
              <Button danger size="small" onClick={handleRevoke}>
                {t("models.revokeAuthorization")}
              </Button>
            )}
            <Button
              size="small"
              icon={<ApiOutlined />}
              onClick={handleTest}
              loading={testing}
            >
              {t("models.testConnection")}
            </Button>
          </div>
          <div className={styles.modalFooterRight}>
            <Button onClick={onClose}>{t("models.cancel")}</Button>
            <Button
              type="primary"
              loading={saving}
              disabled={!formDirty}
              onClick={handleSubmit}
            >
              {t("models.save")}
            </Button>
          </div>
        </div>
      }
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          base_url: provider.current_base_url || undefined,
        }}
        onValuesChange={() => setFormDirty(true)}
      >
        {/* Base URL */}
        <Form.Item
          name="base_url"
          label="Base URL"
          rules={
            canEditBaseUrl
              ? [
                  ...(provider.needs_base_url
                    ? [
                        {
                          required: true,
                          message: t("models.pleaseEnterBaseURL"),
                        },
                      ]
                    : []),
                  {
                    validator: (_: unknown, value: string) => {
                      if (!value?.trim()) return Promise.resolve();
                      try {
                        new URL(value.trim());
                        return Promise.resolve();
                      } catch {
                        return Promise.reject(
                          new Error(t("models.pleaseEnterValidURL")),
                        );
                      }
                    },
                  },
                ]
              : []
          }
          extra={
            canEditBaseUrl
              ? provider.id === "azure-openai"
                ? t("models.azureEndpointHint")
                : t("models.openAIEndpoint")
              : undefined
          }
        >
          <Input
            placeholder={
              canEditBaseUrl
                ? provider.id === "azure-openai"
                  ? "https://<resource>.openai.azure.com/openai/v1"
                  : "http://localhost:11434/v1"
                : ""
            }
            disabled={!canEditBaseUrl}
          />
        </Form.Item>

        {/* API Key */}
        <Form.Item
          name="api_key"
          label="API Key"
          rules={[
            {
              validator: (_, value) => {
                // Reject whitespace-only input
                if (value && !value.trim()) {
                  return Promise.reject(
                    new Error(t("models.apiKeyCannotBeBlank")),
                  );
                }
                // Reject prefix mismatch
                if (
                  value?.trim() &&
                  provider.api_key_prefix &&
                  !value.trim().startsWith(provider.api_key_prefix)
                ) {
                  return Promise.reject(
                    new Error(
                      t("models.apiKeyShouldStart", {
                        prefix: provider.api_key_prefix,
                      }),
                    ),
                  );
                }
                return Promise.resolve();
              },
            },
          ]}
          extra={apiKeyExtra}
        >
          <Input.Password placeholder={apiKeyPlaceholder} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
