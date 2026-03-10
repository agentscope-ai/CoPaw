import { useState, useEffect, useMemo } from "react";
import { SaveOutlined } from "@ant-design/icons";
import { Select, Button, Switch, message } from "@agentscope-ai/design";
import type {
  ActiveModelsInfo,
  AgentsLLMRoutingConfig,
  ModelSlotConfig,
  ModelSlotRequest,
  ProviderInfo,
} from "../../../../../api/types";
import api from "../../../../../api";
import { useTranslation } from "react-i18next";
import styles from "../../index.module.less";

interface ModelsSectionProps {
  providers: ProviderInfo[];
  activeModels: ActiveModelsInfo | null;
  routingConfig: AgentsLLMRoutingConfig | null;
  onSaved: () => void;
}

const EMPTY_SLOT: ModelSlotConfig = {
  provider_id: "",
  model: "",
};

const EMPTY_ROUTING_CONFIG: AgentsLLMRoutingConfig = {
  enabled: false,
  mode: "local_first",
  local: EMPTY_SLOT,
  cloud: null,
};

function getProviderModels(provider?: ProviderInfo) {
  return [...(provider?.models ?? []), ...(provider?.extra_models ?? [])];
}

function isLocalLikeProvider(provider: ProviderInfo) {
  return provider.is_local || provider.id === "ollama";
}

function isConfiguredProvider(provider: ProviderInfo) {
  if (provider.is_local) return true;
  if (provider.id === "ollama") return Boolean(provider.base_url);
  if (provider.is_custom) return Boolean(provider.base_url);
  return Boolean(provider.api_key);
}

function normalizeRoutingConfig(
  config: AgentsLLMRoutingConfig | null,
): AgentsLLMRoutingConfig {
  if (!config) return EMPTY_ROUTING_CONFIG;
  return {
    enabled: Boolean(config.enabled),
    mode: config.mode === "cloud_first" ? "cloud_first" : "local_first",
    local: {
      provider_id: config.local?.provider_id ?? "",
      model: config.local?.model ?? "",
    },
    cloud: null,
  };
}

function resolveRoutingLocalSlot(
  providers: ProviderInfo[],
  currentLocal: ModelSlotConfig,
): ModelSlotConfig | null {
  const candidates = providers.filter(
    (provider) =>
      isLocalLikeProvider(provider) &&
      isConfiguredProvider(provider) &&
      getProviderModels(provider).length > 0,
  );

  if (currentLocal.provider_id && currentLocal.model) {
    const currentProvider = candidates.find(
      (provider) => provider.id === currentLocal.provider_id,
    );
    if (
      currentProvider &&
      getProviderModels(currentProvider).some(
        (model) => model.id === currentLocal.model,
      )
    ) {
      return currentLocal;
    }
  }

  const firstProvider = candidates[0];
  const firstModel = getProviderModels(firstProvider)[0];
  if (!firstProvider || !firstModel) return null;
  return {
    provider_id: firstProvider.id,
    model: firstModel.id,
  };
}

function formatSlotLabel(
  providers: ProviderInfo[],
  slot: ModelSlotConfig | null | undefined,
) {
  if (!slot?.provider_id || !slot.model) return "";
  const provider = providers.find((item) => item.id === slot.provider_id);
  const model = getProviderModels(provider).find((item) => item.id === slot.model);
  const providerLabel = provider?.name ?? slot.provider_id;
  const modelLabel = model?.name ?? slot.model;
  return `${providerLabel} / ${modelLabel}`;
}

export function ModelsSection({
  providers,
  activeModels,
  routingConfig,
  onSaved,
}: ModelsSectionProps) {
  const { t } = useTranslation();
  const [saving, setSaving] = useState(false);
  const [routingSaving, setRoutingSaving] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<
    string | undefined
  >(undefined);
  const [selectedModel, setSelectedModel] = useState<string | undefined>(
    undefined,
  );
  const [dirty, setDirty] = useState(false);
  const [routingEnabled, setRoutingEnabled] = useState(false);
  const [routingMode, setRoutingMode] = useState<
    AgentsLLMRoutingConfig["mode"]
  >("local_first");

  const currentSlot = activeModels?.active_llm;
  const savedRoutingConfig = useMemo(
    () => normalizeRoutingConfig(routingConfig),
    [routingConfig],
  );

  const eligible = useMemo(
    () =>
      providers.filter((p) => {
        const hasModels = getProviderModels(p).length > 0;
        if (!hasModels) return false;
        if (p.is_local) return true;
        if (p.id === "ollama") return !!p.base_url;
        if (p.is_custom) return !!p.base_url;
        return !!p.api_key;
      }),
    [providers],
  );

  useEffect(() => {
    if (currentSlot) {
      setSelectedProviderId(currentSlot.provider_id || undefined);
      setSelectedModel(currentSlot.model || undefined);
    }
    setDirty(false);
  }, [currentSlot?.provider_id, currentSlot?.model]);

  useEffect(() => {
    setRoutingEnabled(savedRoutingConfig.enabled);
    setRoutingMode(savedRoutingConfig.mode);
  }, [savedRoutingConfig]);

  const chosenProvider = providers.find((p) => p.id === selectedProviderId);
  const modelOptions = getProviderModels(chosenProvider);
  const hasModels = modelOptions.length > 0;
  const resolvedLocalSlot = useMemo(
    () => resolveRoutingLocalSlot(providers, savedRoutingConfig.local),
    [providers, savedRoutingConfig.local],
  );
  const routingLocalChanged =
    savedRoutingConfig.local.provider_id !==
      (resolvedLocalSlot?.provider_id ?? "") ||
    savedRoutingConfig.local.model !== (resolvedLocalSlot?.model ?? "");
  const routingDirty =
    routingEnabled !== savedRoutingConfig.enabled ||
    routingMode !== savedRoutingConfig.mode ||
    (routingEnabled && routingLocalChanged);
  const routingStatus = routingEnabled
    ? t("models.routingStatusEnabled")
    : t("models.routingStatusDisabled");
  const localSummary = resolvedLocalSlot
    ? formatSlotLabel(providers, resolvedLocalSlot)
    : t("models.routingNoLocalProviders");
  const remoteFallbackSummary =
    currentSlot?.provider_id && currentSlot?.model
      ? formatSlotLabel(providers, currentSlot)
      : t("models.routingCloudFallbackMissing");

  const handleProviderChange = (pid: string) => {
    setSelectedProviderId(pid);
    setSelectedModel(undefined);
    setDirty(true);
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setDirty(true);
  };

  const handleSave = async () => {
    if (!selectedProviderId || !selectedModel) return;

    const body: ModelSlotRequest = {
      provider_id: selectedProviderId,
      model: selectedModel,
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

  const handleSaveRouting = async () => {
    if (routingEnabled && !resolvedLocalSlot) {
      message.error(t("models.routingLocalRequired"));
      return;
    }

    if (routingEnabled && (!currentSlot?.provider_id || !currentSlot?.model)) {
      message.error(t("models.routingCloudFallbackRequired"));
      return;
    }

    setRoutingSaving(true);
    try {
      await api.updateLlmRoutingConfig({
        enabled: routingEnabled,
        mode: routingMode,
        local: resolvedLocalSlot ?? EMPTY_SLOT,
        cloud: null,
      });
      message.success(t("models.routingSaveSuccess"));
      onSaved();
    } catch (error) {
      const errMsg =
        error instanceof Error ? error.message : t("models.failedToSave");
      message.error(errMsg);
    } finally {
      setRoutingSaving(false);
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

      <div className={styles.routingInline}>
        <div className={styles.slotHeader}>
          <h3 className={styles.slotTitle}>{t("models.routingTitle")}</h3>
          <span className={styles.routingStatus}>{routingStatus}</span>
        </div>

        <p className={styles.routingDescription}>
          {t("models.routingDescription")}
        </p>

        <div className={styles.slotForm}>
          <div className={styles.slotField}>
            <label className={styles.slotLabel}>
              {t("models.routingEnableLabel")}
            </label>
            <div className={styles.routingSwitchRow}>
              <Switch
                checked={routingEnabled}
                disabled={!routingEnabled && !resolvedLocalSlot}
                onChange={setRoutingEnabled}
              />
              <div className={styles.routingSwitchMeta}>
                <span className={styles.routingSwitchTitle}>
                  {routingEnabled
                    ? t("models.routingEnabled")
                    : t("models.routingDisabled")}
                </span>
                <span className={styles.routingSwitchHint}>
                  {t("models.routingEnableHint")}
                </span>
              </div>
            </div>
          </div>

          <div className={styles.slotField}>
            <label className={styles.slotLabel}>
              {t("models.routingModeLabel")}
            </label>
            <Select
              style={{ width: "100%" }}
              value={routingMode}
              onChange={(value) =>
                setRoutingMode(value as AgentsLLMRoutingConfig["mode"])
              }
              options={[
                {
                  value: "local_first",
                  label: t("models.routingModeLocalFirst"),
                },
                {
                  value: "cloud_first",
                  label: t("models.routingModeCloudFirst"),
                },
              ]}
            />
          </div>

          <div className={styles.slotField}>
            <label className={styles.slotLabel}>
              {t("models.routingLocalModelLabel")}
            </label>
            <span className={styles.routingFieldHint}>{localSummary}</span>
          </div>

          <div className={styles.slotField}>
            <label className={styles.slotLabel}>
              {t("models.routingCloudUsesActive")}
            </label>
            <span className={styles.routingFieldHint}>
              {remoteFallbackSummary}
            </span>
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
              loading={routingSaving}
              disabled={!routingDirty}
              onClick={handleSaveRouting}
              block
              icon={<SaveOutlined />}
            >
              {t("models.save")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
