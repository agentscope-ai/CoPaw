import { Select, Space, message } from "antd";
import { RobotOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { agentsApi } from "../../api/modules/agents";
import { useTranslation } from "react-i18next";
import styles from "./index.module.less";

export default function AgentSelector() {
  const { t } = useTranslation();
  const { activeAgent, agents, setActiveAgent, setAgents } = useAgentStore();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await agentsApi.listAgents();
      setAgents(data.agents);
      setActiveAgent(data.active_agent);
    } catch (error) {
      console.error("Failed to load agents:", error);
      message.error(t("agent.loadFailed"));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = async (value: string) => {
    try {
      await agentsApi.activateAgent(value);
      setActiveAgent(value);
      message.success(t("agent.switchSuccess"));
      // Store will notify all components that subscribe to activeAgent
    } catch (error) {
      console.error("Failed to activate agent:", error);
      message.error(t("agent.switchFailed"));
    }
  };

  return (
    <Select
      value={activeAgent}
      onChange={handleChange}
      loading={loading}
      style={{ minWidth: 180 }}
      className={styles.agentSelector}
      placeholder={t("agent.selectAgent")}
      optionLabelProp="label"
    >
      {agents.map((agent) => (
        <Select.Option key={agent.id} value={agent.id} label={agent.name}>
          <Space>
            <RobotOutlined />
            <div>
              <div className={styles.agentName}>{agent.name}</div>
              {agent.description && (
                <div className={styles.agentDescription}>
                  {agent.description}
                </div>
              )}
            </div>
          </Space>
        </Select.Option>
      ))}
    </Select>
  );
}
