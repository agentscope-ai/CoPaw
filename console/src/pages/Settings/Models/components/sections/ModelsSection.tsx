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

interface RoutingSlotOption extends ModelSlotConfig {
  label: string;
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

function getProviderApiKey(provider: ProviderInfo) {
  return provider.current_api_key ?? provider.api_key ?? "";
}

function getProviderBaseUrl(provider: ProviderInfo) {
  return provider.current_base_url ?? provider.base_url ?? "";
}

function isLocalLikeProvider(provider: ProviderInfo) {
  return provider.is_local || provider.id === "ollama";
}

function isConfiguredProvider(provider: ProviderInfo) {
  if (provider.is_local) return true;
  const currentApiKey = getProviderApiKey(provider);
  const currentBaseUrl = getProviderBaseUrl(provider);
  if (provider.id === "ollama") return Boolean(currentBaseUrl);
  if (provider.is_custom) return Boolean(currentBaseUrl);
  if (provider.needs_base_url) {
    return Boolean(currentApiKey) && Boolean(currentBaseUrl);
  }
  return Boolean(currentApiKey);
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
    cloud: config.cloud
      ? {
          provider_id: config.cloud.provider_id ?? "",
          model: config.cloud.model ?? "",
        }
      : null,
  };
}

function buildLocalSlotOptions(providers: ProviderInfo[]): RoutingSlotOption[] {
  return providers.flatMap((provider) => {
    if (
      !isLocalLikeProvider(provider) ||
      !isConfiguredProvider(provider) ||
      getProviderModels(provider).length === 0
    ) {
      return [];
    }
    return getProviderModels(provider).map((model) => ({
      provider_id: provider.id,
      model: model.id,
      label: `${provider.name} / ${model.name}`,
    }));
  });
}

function buildRemoteSlotOptions(
  providers: ProviderInfo[],
): RoutingSlotOption[] {
  return providers.flatMap((provider) => {
    if (
      isLocalLikeProvider(provider) ||
      !isConfiguredProvider(provider) ||
      getProviderModels(provider).length === 0
    ) {
      return [];
    }
    return getProviderModels(provider).map((model) => ({
      provider_id: provider.id,
      model: model.id,
      label: `${provider.name} / ${model.name}`,
    }));
  });
}

function slotKey(slot: ModelSlotConfig | null | undefined) {
  if (!slot?.provider_id || !slot.model) return "";
  return `${slot.provider_id}::${slot.model}`;
}

function resolveRoutingLocalSlot(
  options: RoutingSlotOption[],
  currentLocal: ModelSlotConfig,
): RoutingSlotOption | null {
  const currentKey = slotKey(currentLocal);
  if (currentKey) {
    const currentOption = options.find(
      (option) => slotKey(option) === currentKey,
    );
    if (currentOption) return currentOption;
  }
  return options[0] ?? null;
}

function resolveRoutingCloudSlot(
  options: RoutingSlotOption[],
  currentCloud: ModelSlotConfig | null,
): RoutingSlotOption | null {
  const currentKey = slotKey(currentCloud);
  if (currentKey) {
    const currentOption = options.find(
      (option) => slotKey(option) === currentKey,
    );
    if (currentOption) return currentOption;
  }
  return options[0] ?? null;
}

function formatSlotLabel(
  providers: ProviderInfo[],
  slot: ModelSlotConfig | null | undefined,
) {
  if (!slot?.provider_id || !slot.model) return "";
  const provider = providers.find((item) => item.id === slot.provider_id);
  const model = getProviderModels(provider).find(
    (item) => item.id === slot.model,
  );
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
  const [routingMode, setRoutingMode] =
    useState<AgentsLLMRoutingConfig["mode"]>("local_first");
  const [selectedLocalSlotKey, setSelectedLocalSlotKey] = useState("");
  const [selectedCloudSlotKey, setSelectedCloudSlotKey] = useState("");

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
        return isConfiguredProvider(p);
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
  const savedPrimarySlot =
    currentSlot?.provider_id && currentSlot?.model ? currentSlot : null;
  const currentPrimarySlot =
    selectedProviderId && selectedModel
      ? {
          provider_id: selectedProviderId,
          model: selectedModel,
        }
      : savedPrimarySlot;
  const activeProvider = providers.find(
    (p) => p.id === currentPrimarySlot?.provider_id,
  );
  const activeIsLocalLike = Boolean(
    activeProvider && isLocalLikeProvider(activeProvider),
  );
  const localSlotOptions = useMemo(
    () => buildLocalSlotOptions(providers),
    [providers],
  );
  const remoteSlotOptions = useMemo(
    () => buildRemoteSlotOptions(providers),
    [providers],
  );
  const resolvedLocalSlot = useMemo(
    () => resolveRoutingLocalSlot(localSlotOptions, savedRoutingConfig.local),
    [localSlotOptions, savedRoutingConfig.local],
  );
  const selectedLocalSlot = useMemo(
    () =>
      localSlotOptions.find(
        (option) => slotKey(option) === selectedLocalSlotKey,
      ) ?? resolvedLocalSlot,
    [localSlotOptions, resolvedLocalSlot, selectedLocalSlotKey],
  );
  const resolvedCloudSlot = useMemo(
    () => resolveRoutingCloudSlot(remoteSlotOptions, savedRoutingConfig.cloud),
    [remoteSlotOptions, savedRoutingConfig.cloud],
  );
  const selectedCloudSlot = useMemo(
    () =>
      remoteSlotOptions.find(
        (option) => slotKey(option) === selectedCloudSlotKey,
      ) ?? resolvedCloudSlot,
    [remoteSlotOptions, resolvedCloudSlot, selectedCloudSlotKey],
  );
  const counterpartIsCloud = activeIsLocalLike;
  const selectedCounterpartSlot = counterpartIsCloud
    ? selectedCloudSlot
    : selectedLocalSlot;
  const counterpartOptions = counterpartIsCloud
    ? remoteSlotOptions
    : localSlotOptions;

  useEffect(() => {
    setSelectedLocalSlotKey(slotKey(resolvedLocalSlot));
  }, [resolvedLocalSlot]);

  useEffect(() => {
    setSelectedCloudSlotKey(slotKey(resolvedCloudSlot));
  }, [resolvedCloudSlot]);

  const routingLocalChanged = activeIsLocalLike
    ? savedRoutingConfig.local.provider_id !==
        (currentPrimarySlot?.provider_id ?? "") ||
      savedRoutingConfig.local.model !== (currentPrimarySlot?.model ?? "")
    : savedRoutingConfig.local.provider_id !==
        (selectedLocalSlot?.provider_id ?? "") ||
      savedRoutingConfig.local.model !== (selectedLocalSlot?.model ?? "");
  const routingCloudChanged = counterpartIsCloud
    ? savedRoutingConfig.cloud?.provider_id !==
        (selectedCloudSlot?.provider_id ?? "") ||
      savedRoutingConfig.cloud?.model !== (selectedCloudSlot?.model ?? "")
    : Boolean(
        savedRoutingConfig.cloud?.provider_id ||
          savedRoutingConfig.cloud?.model,
      );
  const routingDirty =
    routingEnabled !== savedRoutingConfig.enabled ||
    routingMode !== savedRoutingConfig.mode ||
    (routingEnabled && routingLocalChanged) ||
    (routingEnabled && routingCloudChanged);
  const routingStatus = routingEnabled
    ? t("models.routingStatusEnabled")
    : t("models.routingStatusDisabled");
  const counterpartSummary = selectedCounterpartSlot
    ? formatSlotLabel(providers, selectedCounterpartSlot)
    : counterpartIsCloud
    ? t("models.routingNoCloudProviders")
    : t("models.routingNoLocalProviders");
  const routingCanEnable = Boolean(
    currentPrimarySlot && selectedCounterpartSlot,
  );
  const counterpartLabel = counterpartIsCloud
    ? t("models.routingCloudModelLabel")
    : t("models.routingLocalModelLabel");
  const counterpartPlaceholder = counterpartIsCloud
    ? t("models.routingSelectCloudModel")
    : t("models.routingSelectLocalModel");

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
    if (routingEnabled && !currentPrimarySlot) {
      message.error(t("models.routingCloudFallbackRequired"));
      return;
    }

    if (routingEnabled && !selectedCounterpartSlot) {
      message.error(
        counterpartIsCloud
          ? t("models.routingCloudRequired")
          : t("models.routingLocalRequired"),
      );
      return;
    }

    setRoutingSaving(true);
    try {
      if (dirty && selectedProviderId && selectedModel) {
        await api.setActiveLlm({
          provider_id: selectedProviderId,
          model: selectedModel,
        });
        setDirty(false);
      }
      await api.updateLlmRoutingConfig({
        enabled: routingEnabled,
        mode: routingMode,
        local: activeIsLocalLike
          ? currentPrimarySlot ?? EMPTY_SLOT
          : selectedLocalSlot ?? EMPTY_SLOT,
        cloud: activeIsLocalLike ? selectedCloudSlot ?? null : null,
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

        <div className={styles.slotForm}>
          <div className={styles.slotField}>
            <label className={styles.slotLabel}>
              {t("models.routingEnableLabel")}
            </label>
            <div className={styles.routingSwitchRow}>
              <Switch
                checked={routingEnabled}
                disabled={!routingEnabled && !routingCanEnable}
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
            <label className={styles.slotLabel}>{counterpartLabel}</label>
            {counterpartOptions.length > 1 ? (
              <Select
                style={{ width: "100%" }}
                value={
                  counterpartIsCloud
                    ? selectedCloudSlotKey || undefined
                    : selectedLocalSlotKey || undefined
                }
                onChange={(value) =>
                  counterpartIsCloud
                    ? setSelectedCloudSlotKey(value)
                    : setSelectedLocalSlotKey(value)
                }
                options={counterpartOptions.map((option) => ({
                  value: slotKey(option),
                  label: option.label,
                }))}
                placeholder={counterpartPlaceholder}
              />
            ) : (
              <span className={styles.routingFieldHint}>
                {counterpartSummary}
              </span>
            )}
          </div>

          <div
            className={styles.slotField}
            style={{ flex: "0 0 auto", minWidth: "120px" }}
          >
            <label
              className={styles.slotLabel}
              style={{ visibility: "hidden" }}
            >
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
