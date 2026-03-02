import { useState, useEffect, useMemo } from "react";
import { SaveOutlined } from "@ant-design/icons";
import { Select, Button, Switch, message } from "@agentscope-ai/design";
import type { ModelSlotRequest } from "../../../../../api/types";
import api from "../../../../../api";
import { useTranslation } from "react-i18next";
import styles from "../../index.module.less";

interface ModelsSectionProps {
  providers: Array<{
    id: string;
    name: string;
    models?: Array<{ id: string; name: string }>;
    extra_models?: Array<{ id: string; name: string }>;
    current_base_url?: string;
    has_api_key: boolean;
    is_custom: boolean;
    is_local?: boolean;
  }>;
  activeModels: {
    active_llm?: {
      provider_id?: string;
      model?: string;
      vision_supported?: boolean;
    };
  } | null;
  onSaved: () => void;
}

export function ModelsSection({
  providers,
  activeModels,
  onSaved,
}: ModelsSectionProps) {
  const { t } = useTranslation();
  const [saving, setSaving] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<
    string | undefined
  >(undefined);
  const [selectedModel, setSelectedModel] = useState<string | undefined>(
    undefined,
  );
  const [dirty, setDirty] = useState(false);

  const currentSlot = activeModels?.active_llm;

  const [selectedVision, setSelectedVision] = useState<boolean>(true);

  const eligible = useMemo(
    () =>
      providers.filter((p) => {
        if (p.is_local) return (p.models?.length ?? 0) > 0;
        return p.is_custom ? !!p.current_base_url : p.has_api_key;
      }),
    [providers],
  );

  useEffect(() => {
    if (currentSlot) {
      setSelectedProviderId(currentSlot.provider_id || undefined);
      setSelectedModel(currentSlot.model || undefined);
      setSelectedVision(currentSlot.vision_supported ?? true);
    }
    setDirty(false);
  }, [
    currentSlot?.provider_id,
    currentSlot?.model,
    currentSlot?.vision_supported,
  ]);

  const chosenProvider = providers.find((p) => p.id === selectedProviderId);
  const modelOptions = chosenProvider?.models ?? [];
  const hasModels = modelOptions.length > 0;

  const handleProviderChange = (pid: string) => {
    setSelectedProviderId(pid);
    setSelectedModel(undefined);
    setDirty(true);
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setDirty(true);
  };

  const handleVisionChange = (checked: boolean) => {
    setSelectedVision(checked);
    setDirty(true);
  };

  const handleSave = async () => {
    if (!selectedProviderId || !selectedModel) return;

    const body: ModelSlotRequest = {
      provider_id: selectedProviderId,
      model: selectedModel,
      vision_supported: selectedVision,
    };

    setSaving(true);
    try {
      await api.setActiveLlm(body);
      message.success(t("models.llmModelUpdated"));
      setDirty(false);
      onSaved();
    } catch (error) {
      const errMsg =
        error instanceof Error ? error.message : t("models.failedToSave");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const isActive =
    currentSlot &&
    currentSlot.provider_id === selectedProviderId &&
    currentSlot.model === selectedModel;
  const canSave = dirty && !!selectedProviderId && !!selectedModel;

  return (
    <div className={styles.slotSection}>
      <div className={styles.slotHeader}>
        <h3 className={styles.slotTitle}>{t("models.llmConfiguration")}</h3>
        {currentSlot?.provider_id && currentSlot?.model && (
          <span className={styles.slotCurrent}>
            {t("models.active", {
              provider: currentSlot.provider_id,
              model: currentSlot.model,
            })}
          </span>
        )}
      </div>

      <div className={styles.slotForm}>
        <div className={styles.slotField}>
          <label className={styles.slotLabel}>{t("models.provider")}</label>
          <Select
            style={{ width: "100%" }}
            placeholder={t("models.selectProvider")}
            value={selectedProviderId}
            onChange={handleProviderChange}
            options={eligible.map((p) => ({
              value: p.id,
              label: p.name,
            }))}
          />
        </div>

        <div className={styles.slotField}>
          <label className={styles.slotLabel}>{t("models.model")}</label>
          <Select
            style={{ width: "100%" }}
            placeholder={
              hasModels ? t("models.selectModel") : t("models.addModelFirst")
            }
            disabled={!hasModels}
            showSearch
            optionFilterProp="label"
            value={selectedModel}
            onChange={handleModelChange}
            options={modelOptions.map((m) => ({
              value: m.id,
              label: `${m.name} (${m.id})`,
            }))}
          />
        </div>

        <div className={styles.slotField}>
          <label className={styles.slotLabel}>
            {t("models.visionSupport")}
          </label>
          <Switch checked={selectedVision} onChange={handleVisionChange} />
        </div>

        <div
          className={styles.slotField}
          style={{ flex: "0 0 auto", minWidth: "120px" }}
        >
          <label className={styles.slotLabel} style={{ visibility: "hidden" }}>
            {t("models.actions")}
          </label>
          <Button
            type="primary"
            loading={saving}
            disabled={!canSave}
            onClick={handleSave}
            block
            icon={<SaveOutlined />}
          >
            {isActive ? t("models.saved") : t("models.save")}
          </Button>
        </div>
      </div>
    </div>
  );
}
