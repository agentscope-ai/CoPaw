import { BrowserWindow } from "electron";

let splashWindow: BrowserWindow | null = null;

const SPLASH_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoPaw</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      width: 420px;
      height: 320px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, "Noto Sans", sans-serif;
      -webkit-app-region: drag;
      user-select: none;
      overflow: hidden;
    }

    .container {
      width: 388px;
      height: 288px;
      background: #ffffff;
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 20px;
      box-shadow: 0px 4px 6px 0px rgba(0, 0, 0, 0.08),
                  0 12px 40px rgba(97, 92, 237, 0.10);
      border: 1px solid #e6e8ee;
      position: relative;
      overflow: hidden;
    }

    .container::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, #615CED, #9189FA, #615CED);
      background-size: 200% 100%;
      animation: gradientSlide 2s ease-in-out infinite;
    }

    @keyframes gradientSlide {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }


    .logo-row {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .logo {
      width: 52px;
      height: 52px;
    }

    .app-name {
      font-size: 26px;
      font-weight: 600;
      color: #26244c;
      letter-spacing: 0.3px;
    }

    .status-row {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 4px;
    }

    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(97, 92, 237, 0.15);
      border-top-color: #615CED;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    #status {
      font-size: 13px;
      color: rgba(38, 36, 76, 0.45);
      letter-spacing: 0.2px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="logo-row">
      <svg class="logo" viewBox="0 0 223.41 300" xmlns="http://www.w3.org/2000/svg">
        <path fill="#26244c" d="M214.95,234.33c-5.66,12.98-13.49,24.33-23.51,34.11-10.02,9.75-21.82,17.46-35.44,23.1-13.6,5.64-28.49,8.46-44.67,8.46s-30.69-2.76-44.31-8.28c-13.6-5.52-25.36-13.1-35.23-22.73-9.89-9.62-17.66-20.94-23.31-33.89-5.66-12.98-8.48-26.9-8.48-41.82v-.75c0-14.89,2.82-28.84,8.48-41.79,5.64-12.98,13.48-24.33,23.49-34.11,10.02-9.75,21.82-17.46,35.44-23.1,13.6-5.64,28.51-8.46,44.69-8.46s30.67,2.76,44.29,8.28c13.6,5.52,25.36,13.07,35.25,22.73,9.87,9.62,17.65,20.91,23.31,33.89,5.64,12.98,8.46,26.9,8.46,41.79v.78c0,14.89-2.82,28.84-8.46,41.79ZM165.64,192.54c0-7.71-1.29-14.95-3.86-21.75-2.57-6.8-6.3-12.85-11.18-18.12-4.87-5.27-10.66-9.44-17.34-12.51-6.68-3.1-14-4.64-21.94-4.64-8.48,0-15.99,1.47-22.54,4.45-6.55,2.95-12.13,6.99-16.76,12.13-4.62,5.14-8.15,11.1-10.6,17.9s-3.65,14.07-3.65,21.75v.78c0,7.71,1.27,14.95,3.84,21.75,2.57,6.8,6.3,12.85,11.18,18.12,4.87,5.27,10.6,9.44,17.15,12.51,6.54,3.07,13.92,4.61,22.15,4.61s15.99-1.47,22.54-4.42c6.54-2.95,12.13-6.99,16.76-12.13,4.61-5.14,8.13-11.1,10.58-17.9s3.67-14.07,3.67-21.79v-.75Z"/>
        <path fill="#615CED" d="M139.13,39.64c-1.5,3.45-3.58,6.46-6.25,9.06-2.66,2.59-5.8,4.64-9.41,6.14-3.61,1.5-7.57,2.25-11.87,2.25s-8.15-.73-11.77-2.2c-3.61-1.47-6.74-3.48-9.36-6.04-2.63-2.56-4.69-5.56-6.19-9-1.5-3.45-2.25-7.14-2.25-11.11v-.2c0-3.96.75-7.66,2.25-11.1,1.5-3.45,3.58-6.46,6.24-9.06,2.66-2.59,5.8-4.64,9.41-6.14,3.61-1.5,7.57-2.25,11.87-2.25s8.15.73,11.77,2.2c3.61,1.47,6.74,3.47,9.36,6.04,2.62,2.56,4.69,5.55,6.19,9,1.5,3.45,2.25,7.14,2.25,11.1v.21c0,3.96-.75,7.66-2.25,11.1Z"/>
        <path fill="#615CED" d="M66.94,60.78c-1.5,3.45-3.58,6.46-6.25,9.06-2.66,2.59-5.8,4.64-9.41,6.14-3.61,1.5-7.57,2.25-11.87,2.25s-8.15-.73-11.77-2.2c-3.61-1.47-6.74-3.48-9.36-6.04-2.63-2.56-4.69-5.56-6.19-9-1.5-3.45-2.25-7.14-2.25-11.11v-.2c0-3.96.75-7.66,2.25-11.1,1.5-3.45,3.58-6.46,6.24-9.06,2.66-2.59,5.8-4.64,9.41-6.14,3.61-1.5,7.57-2.25,11.87-2.25s8.15.73,11.77,2.2c3.61,1.47,6.74,3.47,9.36,6.04,2.62,2.56,4.69,5.55,6.19,9,1.5,3.45,2.25,7.14,2.25,11.1v.21c0,3.96-.75,7.66-2.25,11.1Z"/>
        <path fill="#615CED" d="M211.32,60.78c-1.5,3.45-3.58,6.46-6.25,9.06-2.66,2.59-5.8,4.64-9.41,6.14-3.61,1.5-7.57,2.25-11.87,2.25s-8.15-.73-11.77-2.2c-3.61-1.47-6.74-3.48-9.36-6.04-2.63-2.56-4.69-5.56-6.19-9-1.5-3.45-2.25-7.14-2.25-11.11v-.2c0-3.96.75-7.66,2.25-11.1,1.5-3.45,3.58-6.46,6.24-9.06,2.66-2.59,5.8-4.64,9.41-6.14,3.61-1.5,7.57-2.25,11.87-2.25s8.15.73,11.77,2.2c3.61,1.47,6.74,3.47,9.36,6.04,2.62,2.56,4.69,5.55,6.19,9,1.5,3.45,2.25,7.14,2.25,11.1v.21c0,3.96-.75,7.66-2.25,11.1Z"/>
      </svg>
      <span class="app-name">CoPaw</span>
    </div>
    <div class="status-row">
      <div class="spinner"></div>
      <span id="status">Starting</span>
    </div>
  </div>
</body>
</html>`;

export function showSplash(): BrowserWindow {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 320,
    frame: false,
    transparent: true,
    hasShadow: false,
    resizable: false,
    center: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  splashWindow.loadURL(
    `data:text/html;charset=utf-8,${encodeURIComponent(SPLASH_HTML)}`,
  );

  splashWindow.on("closed", () => {
    splashWindow = null;
  });

  return splashWindow;
}

export function updateSplashStatus(message: string): void {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.executeJavaScript(
      `document.getElementById('status')&&(document.getElementById('status').textContent=${JSON.stringify(message)})`,
    );
  }
}

export function closeSplash(): void {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
    splashWindow = null;
  }
}
