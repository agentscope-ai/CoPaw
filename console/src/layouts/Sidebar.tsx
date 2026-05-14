import {
  Layout,
  Menu,
  Button,
  Modal,
  Input,
  Form,
  Tooltip,
  Badge,
  type MenuProps,
} from "antd";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAppMessage } from "../hooks/useAppMessage";
import AgentSelector from "../components/AgentSelector";
import {
  SparkChatTabFill,
  SparkWifiLine,
  SparkUserGroupLine,
  SparkDateLine,
  SparkVoiceChat01Line,
  SparkMagicWandLine,
  SparkLocalFileLine,
  SparkModePlazaLine,
  SparkInternetLine,
  SparkModifyLine,
  SparkBrowseLine,
  SparkMcpMcpLine,
  SparkScanLine,
  SparkToolLine,
  SparkDataLine,
  SparkMicLine,
  SparkAgentLine,
  SparkExitFullscreenLine,
  SparkSearchUserLine,
  SparkMenuExpandLine,
  SparkMenuFoldLine,
  SparkOtherLine,
  SparkBarChartLine,
  SparkDebugLine,
  SparkSaveLine,
} from "@agentscope-ai/icons";
import { Package } from "lucide-react";
import { clearAuthToken } from "../api/config";
import { authApi } from "../api/modules/auth";
import api from "../api";
import { usePlugins } from "../plugins/PluginContext";
import { useMobileNav } from "../contexts/MobileNavContext";
import styles from "./index.module.less";
import { useTheme } from "../contexts/ThemeContext";
import { KEY_TO_PATH, DEFAULT_OPEN_KEYS } from "./constants";

// ── Layout ────────────────────────────────────────────────────────────────

const { Sider } = Layout;
const INBOX_BADGE_POLLING_MS = 6000;

// ── Types ─────────────────────────────────────────────────────────────────

interface SidebarProps {
  selectedKey: string;
}

// ── Sidebar ───────────────────────────────────────────────────────────────

export default function Sidebar({ selectedKey }: SidebarProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { isDark } = useTheme();
  const { pluginRoutes } = usePlugins();
  const { isMobile, sidebarOpen, closeSidebar } = useMobileNav();
  const [authEnabled, setAuthEnabled] = useState(false);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [accountLoading, setAccountLoading] = useState(false);
  const [accountForm] = Form.useForm();
  const [collapsed, setCollapsed] = useState(false);
  const [hasInboxUnread, setHasInboxUnread] = useState(false);

  // On mobile we never render the collapsed rail — the entire sidebar is an
  // off-canvas drawer, so force-expand while mobile is active.
  const effectiveCollapsed = isMobile ? false : collapsed;

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) closeSidebar();
  };

  // ── Effects ──────────────────────────────────────────────────────────────

  useEffect(() => {
    authApi
      .getStatus()
      .then((res) => setAuthEnabled(res.enabled))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const loadUnreadState = async () => {
      try {
        const [inboxRes, pushRes] = await Promise.all([
          api.getInboxEvents({
            unread_only: true,
            limit: 1,
          }),
          api.getPushMessages(),
        ]);
        const hasUnreadEvents = (inboxRes?.events?.length || 0) > 0;
        const hasPendingApprovals =
          (pushRes?.pending_approvals?.length || 0) > 0;
        setHasInboxUnread(hasUnreadEvents || hasPendingApprovals);
      } catch {
        // Keep previous state when polling fails.
      }
    };
    void loadUnreadState();
    const timer = window.setInterval(() => {
      void loadUnreadState();
    }, INBOX_BADGE_POLLING_MS);
    return () => window.clearInterval(timer);
  }, []);

  const inboxIcon = (size: number) => (
    <Badge dot={hasInboxUnread} color="rgba(255, 157, 77, 1)" offset={[2, 0]}>
      <SparkOtherLine size={size} />
    </Badge>
  );
  const inboxLabel = collapsed ? null : (
    <Badge dot={hasInboxUnread} color="rgba(255, 157, 77, 1)" offset={[5, 7]}>
      <span>{t("nav.inbox")}</span>
    </Badge>
  );
  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleUpdateProfile = async (values: {
    currentPassword: string;
    newUsername?: string;
    newPassword?: string;
  }) => {
    const trimmedUsername = values.newUsername?.trim() || undefined;
    const trimmedPassword = values.newPassword?.trim() || undefined;

    if (values.newPassword && !trimmedPassword) {
      message.error(t("account.passwordEmpty"));
      return;
    }

    if (values.newUsername && !trimmedUsername) {
      message.error(t("account.usernameEmpty"));
      return;
    }

    if (!trimmedUsername && !trimmedPassword) {
      message.warning(t("account.nothingToUpdate"));
      return;
    }

    setAccountLoading(true);
    try {
      await authApi.updateProfile(
        values.currentPassword,
        trimmedUsername,
        trimmedPassword,
      );
      message.success(t("account.updateSuccess"));
      setAccountModalOpen(false);
      accountForm.resetFields();
      clearAuthToken();
      window.location.href = "/login";
    } catch (err: unknown) {
      const raw = err instanceof Error ? err.message : "";
      let msg = t("account.updateFailed");
      if (raw.includes("password is incorrect")) {
        msg = t("account.wrongPassword");
      } else if (raw.includes("Nothing to update")) {
        msg = t("account.nothingToUpdate");
      } else if (raw.includes("cannot be empty")) {
        msg = t("account.nothingToUpdate");
      } else if (raw) {
        msg = raw;
      }
      message.error(msg);
    } finally {
      setAccountLoading(false);
    }
  };

  // ── Collapsed nav items (all leaf pages) ──────────────────────────────

  const collapsedNavItems = [
    {
      key: "chat",
      icon: <SparkChatTabFill size={18} />,
      path: "/chat",
      label: t("nav.chat"),
    },
    {
      key: "inbox",
      icon: inboxIcon(18),
      path: "/inbox",
      label: t("nav.inbox"),
    },
    {
      key: "channels",
      icon: <SparkWifiLine size={18} />,
      path: "/channels",
      label: t("nav.channels"),
    },
    {
      key: "sessions",
      icon: <SparkUserGroupLine size={18} />,
      path: "/sessions",
      label: t("nav.sessions"),
    },
    {
      key: "cron-jobs",
      icon: <SparkDateLine size={18} />,
      path: "/cron-jobs",
      label: t("nav.cronJobs"),
    },
    {
      key: "heartbeat",
      icon: <SparkVoiceChat01Line size={18} />,
      path: "/heartbeat",
      label: t("nav.heartbeat"),
    },
    {
      key: "workspace",
      icon: <SparkLocalFileLine size={18} />,
      path: "/workspace",
      label: t("nav.workspace"),
    },
    {
      key: "skills",
      icon: <SparkMagicWandLine size={18} />,
      path: "/skills",
      label: t("nav.skills"),
    },
    {
      key: "skill-pool",
      icon: <SparkOtherLine size={18} />,
      path: "/skill-pool",
      label: t("nav.skillPool", "Skill Pool"),
    },
    {
      key: "tools",
      icon: <SparkToolLine size={18} />,
      path: "/tools",
      label: t("nav.tools"),
    },
    {
      key: "mcp",
      icon: <SparkMcpMcpLine size={18} />,
      path: "/mcp",
      label: t("nav.mcp"),
    },
    {
      key: "acp",
      icon: <SparkScanLine size={18} />,
      path: "/acp",
      label: t("nav.acp"),
    },
    {
      key: "agent-config",
      icon: <SparkModifyLine size={18} />,
      path: "/agent-config",
      label: t("nav.agentConfig"),
    },
    {
      key: "agent-stats",
      icon: <SparkBarChartLine size={18} />,
      path: "/agent-stats",
      label: t("nav.agentStats"),
    },
    {
      key: "agents",
      icon: <SparkAgentLine size={18} />,
      path: "/agents",
      label: t("nav.agents"),
    },
    {
      key: "models",
      icon: <SparkModePlazaLine size={18} />,
      path: "/models",
      label: t("nav.models"),
    },
    {
      key: "environments",
      icon: <SparkInternetLine size={18} />,
      path: "/environments",
      label: t("nav.environments"),
    },
    {
      key: "security",
      icon: <SparkBrowseLine size={18} />,
      path: "/security",
      label: t("nav.security"),
    },
    {
      key: "token-usage",
      icon: <SparkDataLine size={18} />,
      path: "/token-usage",
      label: t("nav.tokenUsage"),
    },
    {
      key: "backups",
      icon: <SparkSaveLine size={18} />,
      path: "/backups",
      label: t("nav.backups"),
    },
    {
      key: "voice-transcription",
      icon: <SparkMicLine size={18} />,
      path: "/voice-transcription",
      label: t("nav.voiceTranscription"),
    },
    {
      key: "debug",
      icon: <SparkDebugLine size={18} />,
      path: "/debug",
      label: t("nav.debug", "Debug"),
    },
    {
      key: "plugin-manager",
      icon: <Package size={18} />,
      path: "/plugin-manager",
      label: t("nav.pluginManager", "Plugin Manager"),
    },
    // Append plugin nav items dynamically
    ...pluginRoutes.map((route) => ({
      key: route.path.replace(/^\//, ""),
      icon: <span style={{ fontSize: 18 }}>{route.icon}</span>,
      path: route.path,
      label: route.label,
    })),
  ];

  // ── Menu items — agent-scoped (Chat + Control + Workspace) ──────────────

  const agentMenuItems: MenuProps["items"] = [
    {
      key: "inbox",
      label: inboxLabel,
      icon: <SparkOtherLine size={16} />,
    },
    {
      key: "control-group",
      label: effectiveCollapsed ? null : t("nav.control"),
      children: [
        {
          key: "channels",
          label: effectiveCollapsed ? null : t("nav.channels"),
          icon: <SparkWifiLine size={16} />,
        },
        {
          key: "sessions",
          label: effectiveCollapsed ? null : t("nav.sessions"),
          icon: <SparkUserGroupLine size={16} />,
        },
        {
          key: "cron-jobs",
          label: effectiveCollapsed ? null : t("nav.cronJobs"),
          icon: <SparkDateLine size={16} />,
        },
        {
          key: "heartbeat",
          label: effectiveCollapsed ? null : t("nav.heartbeat"),
          icon: <SparkVoiceChat01Line size={16} />,
        },
      ],
    },
    {
      key: "agent-group",
      label: effectiveCollapsed ? null : t("nav.agent"),
      children: [
        {
          key: "workspace",
          label: effectiveCollapsed ? null : t("nav.workspace"),
          icon: <SparkLocalFileLine size={16} />,
        },
        {
          key: "skills",
          label: effectiveCollapsed ? null : t("nav.skills"),
          icon: <SparkMagicWandLine size={16} />,
        },
        {
          key: "tools",
          label: effectiveCollapsed ? null : t("nav.tools"),
          icon: <SparkToolLine size={16} />,
        },
        {
          key: "mcp",
          label: effectiveCollapsed ? null : t("nav.mcp"),
          icon: <SparkMcpMcpLine size={16} />,
        },
        {
          key: "acp",
          label: effectiveCollapsed ? null : t("nav.acp"),
          icon: <SparkScanLine size={16} />,
        },
        {
          key: "agent-config",
          label: effectiveCollapsed ? null : t("nav.agentConfig"),
          icon: <SparkModifyLine size={16} />,
        },
        {
          key: "agent-stats",
          label: effectiveCollapsed ? null : t("nav.agentStats"),
          icon: <SparkBarChartLine size={16} />,
        },
      ],
    },
  ];

  // ── Menu items — global settings ──────────────────────────────────────

  const settingsMenuItems: MenuProps["items"] = [
    {
      key: "settings-group",
      label: effectiveCollapsed ? null : t("nav.settings"),
      children: [
        {
          key: "agents",
          label: effectiveCollapsed ? null : t("nav.agents"),
          icon: <SparkAgentLine size={16} />,
        },
        {
          key: "models",
          label: effectiveCollapsed ? null : t("nav.models"),
          icon: <SparkModePlazaLine size={16} />,
        },
        {
          key: "skill-pool",
          label: effectiveCollapsed ? null : t("nav.skillPool", "Skill Pool"),
          icon: <SparkOtherLine size={16} />,
        },
        {
          key: "environments",
          label: effectiveCollapsed ? null : t("nav.environments"),
          icon: <SparkInternetLine size={16} />,
        },
        {
          key: "security",
          label: effectiveCollapsed ? null : t("nav.security"),
          icon: <SparkBrowseLine size={16} />,
        },
        {
          key: "token-usage",
          label: effectiveCollapsed ? null : t("nav.tokenUsage"),
          icon: <SparkDataLine size={16} />,
        },
        {
          key: "backups",
          label: effectiveCollapsed ? null : t("nav.backups"),
          icon: <SparkSaveLine size={16} />,
        },
        {
          key: "voice-transcription",
          label: effectiveCollapsed ? null : t("nav.voiceTranscription"),
          icon: <SparkMicLine size={16} />,
        },
        {
          key: "debug",
          label: effectiveCollapsed ? null : t("nav.debug", "Debug"),
          icon: <SparkDebugLine size={16} />,
        },
        {
          key: "plugin-manager",
          label: collapsed ? null : t("nav.pluginManager", "Plugin Manager"),
          icon: <Package size={16} />,
        },
      ],
    },
  ];

  // Append plugin menu items as a group (only when there are plugins)
  if (pluginRoutes.length > 0) {
    settingsMenuItems.push({
      key: "plugins-group",
      label: effectiveCollapsed ? null : t("nav.plugins"),
      children: pluginRoutes.map((route) => ({
        key: route.path.replace(/^\//, ""),
        label: effectiveCollapsed ? null : route.label,
        icon: <span style={{ fontSize: 16 }}>{route.icon}</span>,
      })),
    } as any);
  }

  // ── Render ────────────────────────────────────────────────────────────────

  // On mobile we always render the *expanded* markup, plus extra classes so
  // mobile.css can turn the Sider into an off-canvas drawer.
  const mobileClassNames = isMobile
    ? ` qwenpaw-console-sidebar-mobile${
        sidebarOpen ? " qwenpaw-console-sidebar-open" : ""
      }`
    : "";

  const siderWidth = collapsed ? (isMobile ? 56 : 72) : 240;

  return (
    <Sider
      width={siderWidth}
      className={`${styles.sider}${
        effectiveCollapsed ? ` ${styles.siderCollapsed}` : ""
      }${isDark ? ` ${styles.siderDark}` : ""}${mobileClassNames}`}
    >
      {effectiveCollapsed ? (
        <nav className={styles.collapsedNav}>
          {collapsedNavItems.map((item) => {
            const isActive = selectedKey === item.key;
            return (
              <Tooltip
                key={item.key}
                title={item.label}
                placement="right"
                overlayInnerStyle={{
                  background: "rgba(0,0,0,0.75)",
                  color: "#fff",
                }}
              >
                <button
                  className={`${styles.collapsedNavItem} ${
                    isActive ? styles.collapsedNavItemActive : ""
                  }`}
                  onClick={() => handleNavigate(item.path)}
                >
                  {item.icon}
                </button>
              </Tooltip>
            );
          })}
        </nav>
      ) : (
        <>
          {/* Agent-scoped section: selector + Chat + Control + Workspace */}
          <div className={styles.agentScopedSection}>
            <div className={styles.agentSelectorContainer}>
              <AgentSelector collapsed={collapsed} />
              {/* Chat entry — sticky together with agent selector */}
              <button
                className={`${styles.stickyChatButton}${
                  selectedKey === "chat"
                    ? ` ${styles.stickyChatButtonActive}`
                    : ""
                }`}
                onClick={() => navigate("/chat")}
              >
                <SparkChatTabFill size={16} />
                <span>{t("nav.chat")}</span>
              </button>
            </div>
            <Menu
              mode="inline"
              selectedKeys={[selectedKey]}
              openKeys={DEFAULT_OPEN_KEYS}
              onClick={({ key }) => {
                const path = KEY_TO_PATH[String(key)];
                if (path) handleNavigate(path);
              }}
              items={agentMenuItems}
              theme={isDark ? "dark" : "light"}
              className={styles.sideMenu}
            />
          </div>

          {/* Global settings section */}
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            openKeys={[
              ...DEFAULT_OPEN_KEYS,
              ...(pluginRoutes.length > 0 ? ["plugins-group"] : []),
            ]}
            onClick={({ key }) => {
              const path = KEY_TO_PATH[String(key)] ?? `/${String(key)}`;
              handleNavigate(path);
            }}
            items={settingsMenuItems}
            theme={isDark ? "dark" : "light"}
            className={styles.sideMenu}
          />
        </>
      )}

      {authEnabled && !effectiveCollapsed && (
        <div className={styles.authActions}>
          <Button
            type="text"
            icon={<SparkSearchUserLine size={16} />}
            onClick={() => {
              accountForm.resetFields();
              setAccountModalOpen(true);
            }}
            block
            className={`${styles.authBtn} ${
              effectiveCollapsed ? styles.authBtnCollapsed : ""
            }`}
          >
            {!effectiveCollapsed && t("account.title")}
          </Button>
          <Button
            type="text"
            icon={<SparkExitFullscreenLine size={16} />}
            onClick={() => {
              clearAuthToken();
              window.location.href = "/login";
            }}
            block
            className={`${styles.authBtn} ${
              effectiveCollapsed ? styles.authBtnCollapsed : ""
            }`}
          >
            {!effectiveCollapsed && t("login.logout")}
          </Button>
        </div>
      )}

      {!isMobile && (
        <div
          className={`${styles.collapseToggleContainer} qwenpaw-console-sidebar-desktop-collapse`}
        >
          <Button
            type="text"
            icon={
              effectiveCollapsed ? (
                <SparkMenuExpandLine size={20} />
              ) : (
                <SparkMenuFoldLine size={20} />
              )
            }
            onClick={() => setCollapsed(!collapsed)}
            className={styles.collapseToggle}
          />
        </div>
      )}

      <Modal
        open={accountModalOpen}
        onCancel={() => setAccountModalOpen(false)}
        title={t("account.title")}
        footer={null}
        destroyOnHidden
        centered
      >
        <Form
          form={accountForm}
          layout="vertical"
          onFinish={handleUpdateProfile}
        >
          <Form.Item
            name="currentPassword"
            label={t("account.currentPassword")}
            rules={[
              { required: true, message: t("account.currentPasswordRequired") },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="newUsername" label={t("account.newUsername")}>
            <Input placeholder={t("account.newUsernamePlaceholder")} />
          </Form.Item>
          <Form.Item name="newPassword" label={t("account.newPassword")}>
            <Input.Password placeholder={t("account.newPasswordPlaceholder")} />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            label={t("account.confirmPassword")}
            dependencies={["newPassword"]}
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value && !getFieldValue("newPassword")) {
                    return Promise.resolve();
                  }
                  if (value === getFieldValue("newPassword")) {
                    return Promise.resolve();
                  }
                  return Promise.reject(
                    new Error(t("account.passwordMismatch")),
                  );
                },
              }),
            ]}
          >
            <Input.Password
              placeholder={t("account.confirmPasswordPlaceholder")}
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={accountLoading}
              block
            >
              {t("account.save")}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Sider>
  );
}
