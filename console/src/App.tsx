import { createGlobalStyle } from "antd-style";
import { ConfigProvider, bailianTheme } from "@agentscope-ai/design";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import MainLayout from "./layouts/MainLayout";
import LoginPage from "./pages/Login";
import { authApi } from "./api/modules/auth";
import { getApiToken, clearAuthToken } from "./api/config";
import "./styles/layout.css";
import "./styles/form-override.css";

const GlobalStyle = createGlobalStyle`
* {
  margin: 0;
  box-sizing: border-box;
}
`;

function AuthGuard({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<
    "loading" | "auth-required" | "ok"
  >("loading");

  useEffect(() => {
    authApi
      .getStatus()
      .then((res) => {
        if (!res.enabled) {
          setStatus("ok");
          return;
        }
        // Auth is enabled, check if we have a valid token
        const token = getApiToken();
        if (!token) {
          setStatus("auth-required");
          return;
        }
        // Verify token by making a simple API call
        fetch("/api/version", {
          headers: { Authorization: `Bearer ${token}` },
        }).then((r) => {
          if (r.ok) {
            setStatus("ok");
          } else {
            clearAuthToken();
            setStatus("auth-required");
          }
        });
      })
      .catch(() => {
        // If we can't reach the server, let them through
        setStatus("ok");
      });
  }, []);

  if (status === "loading") return null;
  if (status === "auth-required")
    return <Navigate to={`/login?redirect=${encodeURIComponent(window.location.pathname)}`} replace />;
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <GlobalStyle />
      <ConfigProvider {...bailianTheme} prefix="copaw" prefixCls="copaw">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <AuthGuard>
                <MainLayout />
              </AuthGuard>
            }
          />
        </Routes>
      </ConfigProvider>
    </BrowserRouter>
  );
}

export default App;
