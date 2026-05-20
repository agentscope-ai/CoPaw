import { useCallback, useState } from "react";
import { Modal, Tooltip } from "antd";
import { Code, FlaskConical, MessageSquare } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useCodingMode } from "../../stores/codingModeStore";
import { useAgentStore } from "../../stores/agentStore";
import { getApiUrl } from "../../api/config";
import { buildAuthHeaders } from "../../api/authHeaders";
import { useNavigate } from "react-router-dom";
import styles from "./index.module.less";

const CONFIRMED_KEY = "qwenpaw-coding-mode-confirmed";

export default function CodingModeToggle() {
  const { t } = useTranslation();
  const { codingMode, setCodingMode } = useCodingMode();
  const { selectedAgent } = useAgentStore();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const activate = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    try {
      await fetch(getApiUrl("/coding-mode"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          "X-Agent-Id": selectedAgent,
        },
        body: JSON.stringify({ enabled: true }),
      });
      setCodingMode(true);
      navigate("/coding");
    } catch {
      // Silently ignore
    } finally {
      setLoading(false);
    }
  }, [loading, selectedAgent, setCodingMode, navigate]);

  const deactivate = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    try {
      await fetch(getApiUrl("/coding-mode"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          "X-Agent-Id": selectedAgent,
        },
        body: JSON.stringify({ enabled: false }),
      });
      setCodingMode(false);
      navigate("/chat");
    } catch {
      // Silently ignore
    } finally {
      setLoading(false);
    }
  }, [loading, selectedAgent, setCodingMode, navigate]);

  const toggle = useCallback(async () => {
    if (codingMode) {
      // Exiting doesn't need confirmation
      await deactivate();
      return;
    }
    // First-time activation: show experimental warning
    const confirmed = localStorage.getItem(CONFIRMED_KEY);
    if (!confirmed) {
      setShowConfirm(true);
    } else {
      await activate();
    }
  }, [codingMode, activate, deactivate]);

  const handleConfirm = useCallback(async () => {
    localStorage.setItem(CONFIRMED_KEY, "1");
    setShowConfirm(false);
    await activate();
  }, [activate]);

  return (
    <>
      <Tooltip
        title={codingMode ? t("codingMode.exitTooltip") : t("codingMode.enterTooltip")}
        placement="bottom"
      >
        <button
          type="button"
          className={`${styles.toggle} ${codingMode ? styles.active : ""}`}
          onClick={toggle}
          disabled={loading}
          aria-label={codingMode ? t("codingMode.exitTooltip") : t("codingMode.enterTooltip")}
        >
          <span className={styles.icon}>
            {codingMode ? <MessageSquare size={14} /> : <Code size={14} />}
          </span>
          <span className={styles.label}>
            {codingMode ? t("common.cancel", { defaultValue: "Chat" }) : "Code"}
          </span>
        </button>
      </Tooltip>

      <Modal
        open={showConfirm}
        title={
          <span className={styles.modalTitle}>
            <FlaskConical size={16} className={styles.flaskIcon} />
            {t("codingMode.experimental")}
          </span>
        }
        okText={t("codingMode.confirmBtn")}
        cancelText={t("common.cancel")}
        onOk={() => void handleConfirm()}
        onCancel={() => setShowConfirm(false)}
        confirmLoading={loading}
        width={440}
      >
        <div className={styles.modalBody}>
          <p className={styles.modalDesc}>{t("codingMode.experimentalDesc")}</p>
          <p className={styles.modalNote}>{t("codingMode.experimentalNote")}</p>
        </div>
      </Modal>
    </>
  );
}
