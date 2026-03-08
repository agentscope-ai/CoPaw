import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button, Card, Form, Input, message } from "antd";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { authApi } from "../../api/modules/auth";
import { setAuthToken } from "../../api/config";

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const res = await authApi.login(values.username, values.password);
      const raw = searchParams.get("redirect") || "/chat";
      // Only allow relative paths to prevent open redirect
      const redirect =
        raw.startsWith("/") && !raw.startsWith("//") ? raw : "/chat";
      if (res.token) {
        setAuthToken(res.token);
        navigate(redirect, { replace: true });
      } else {
        message.info(t("login.authNotEnabled"));
        navigate(redirect, { replace: true });
      }
    } catch {
      message.error(t("login.failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: "0 4px 24px rgba(0,0,0,0.1)",
          borderRadius: 12,
        }}
      >
        <div
          style={{
            textAlign: "center",
            marginBottom: 32,
          }}
        >
          <img
            src="/logo.png"
            alt="CoPaw"
            style={{ height: 48, marginBottom: 12 }}
          />
          <h2 style={{ margin: 0, fontWeight: 600, fontSize: 20 }}>
            {t("login.title")}
          </h2>
        </div>

        <Form
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: t("login.usernameRequired") }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder={t("login.usernamePlaceholder")}
              autoFocus
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: t("login.passwordRequired") }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={t("login.passwordPlaceholder")}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 44, borderRadius: 8, fontWeight: 500 }}
            >
              {t("login.submit")}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
