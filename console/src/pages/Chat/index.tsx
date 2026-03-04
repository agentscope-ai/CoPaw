import {
  AgentScopeRuntimeWebUI,
  IAgentScopeRuntimeWebUIOptions,
} from "@agentscope-ai/chat";
import { useEffect, useMemo, useState } from "react";
import { Modal, Button, Result, Spin } from "antd";
import { ExclamationCircleOutlined, SettingOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import sessionApi from "./sessionApi";
import { useLocalStorageState } from "ahooks";
import defaultConfig, { DefaultConfig } from "./OptionsPanel/defaultConfig";
import Weather from "./Weather";
import { getApiUrl, getApiToken } from "../../api/config";
import { providerApi } from "../../api/modules/provider";
import "./index.module.less";

interface CustomWindow extends Window {
  currentSessionId?: string;
  currentUserId?: string;
  currentChannel?: string;
}

declare const window: CustomWindow;

type OptionsConfig = DefaultConfig;

export default function ChatPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [showModelPrompt, setShowModelPrompt] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [optionsConfig] = useLocalStorageState<OptionsConfig>(
    "agent-scope-runtime-webui-options",
    {
      defaultValue: defaultConfig,
      listenStorageChange: true,
    },
  );

  const handleConfigureModel = () => {
    setShowModelPrompt(false);
    navigate("/models");
  };

  const handleSkipConfiguration = () => {
    setShowModelPrompt(false);
  };

  useEffect(() => {
    let disposed = false;
    const startedAt = Date.now();

    const preload = async () => {
      // 主动预加载会话列表，不依赖组件库触发
      await sessionApi.getSessionList();

      const elapsed = Date.now() - startedAt;
      const minVisible = 500;
      const rest = Math.max(0, minVisible - elapsed);
      if (rest > 0) {
        await new Promise((resolve) => setTimeout(resolve, rest));
      }
      if (!disposed) {
        setBootLoading(false);
      }
    };

    preload();
    return () => {
      disposed = true;
    };
  }, []);

  const options = useMemo(() => {
    const handleModelError = () => {
      setShowModelPrompt(true);
      return new Response(
        JSON.stringify({
          error: "Model not configured",
          message: "Please configure a model first",
        }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        },
      );
    };

    const customFetch = async (data: {
      input: any[];
      biz_params?: any;
      signal?: AbortSignal;
    }): Promise<Response> => {
      try {
        const activeModels = await providerApi.getActiveModels();

        if (
          !activeModels?.active_llm?.provider_id ||
          !activeModels?.active_llm?.model
        ) {
          return handleModelError();
        }
      } catch (error) {
        console.error("Failed to check model configuration:", error);
        return handleModelError();
      }

      const { input, biz_params } = data;

      const lastMessage = input[input.length - 1];
      const session = lastMessage?.session || {};

      const session_id = window.currentSessionId || session?.session_id || "";
      const user_id = window.currentUserId || session?.user_id || "default";
      const channel = window.currentChannel || session?.channel || "console";

      const requestBody = {
        input: input.slice(-1),
        session_id,
        user_id,
        channel,
        stream: true,
        ...biz_params,
      };

      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      const token = getApiToken();
      if (token) {
        (headers as Record<string, string>).Authorization = `Bearer ${token}`;
      }

      const url = optionsConfig?.api?.baseURL || getApiUrl("/agent/process");
      return fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(requestBody),
        signal: data.signal,
      });
    };

    return {
      ...optionsConfig,
      session: {
        multiple: true,
        api: sessionApi,
      },
      theme: {
        ...optionsConfig.theme,
      },
      api: {
        ...optionsConfig.api,
        fetch: customFetch,
        cancel(data: { session_id: string }) {
          console.log(data);
        },
      },
      customToolRenderConfig: {
        "weather search mock": Weather,
      },
    } as unknown as IAgentScopeRuntimeWebUIOptions;
  }, [optionsConfig]);

  if (bootLoading) {
    return (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(245, 247, 250, 0.98)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <Spin size="large" />
          <div style={{ marginTop: 14, color: "#3e4466", fontSize: 14 }}>
            {t("common.loading")}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      <AgentScopeRuntimeWebUI options={options} />

      <Modal open={showModelPrompt} closable={false} footer={null} width={480}>
        <Result
          icon={<ExclamationCircleOutlined style={{ color: "#faad14" }} />}
          title={t("modelConfig.promptTitle")}
          subTitle={t("modelConfig.promptMessage")}
          extra={[
            <Button key="skip" onClick={handleSkipConfiguration}>
              {t("modelConfig.skipButton")}
            </Button>,
            <Button
              key="configure"
              type="primary"
              icon={<SettingOutlined />}
              onClick={handleConfigureModel}
            >
              {t("modelConfig.configureButton")}
            </Button>,
          ]}
        />
      </Modal>
    </div>
  );
}
