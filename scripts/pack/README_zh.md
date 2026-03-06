# CoPaw Desktop 打包脚本

一键打包：脚本会自动构建 console 前端，再用 **临时 conda 环境** + **conda-pack**（不依赖当前开发环境）。依赖以 `pyproject.toml` 为准。

- **Windows**: console → conda-pack → 解压 → NSIS 安装包 (`.exe`)
- **macOS**: console → conda-pack → 解压到 `.app` → 可选打 zip

## 前置

- **conda**（Miniconda/Anaconda）在 PATH
- **Node.js / npm**（用于构建 console 前端）
- （仅 Windows）**NSIS**：`makensis` 在 PATH
- （macOS 可选）图标：若有 `scripts/pack/assets/icon.svg`，可先运行一次 `python scripts/pack/gen_icon_icns.py` 生成 `icon.icns`

## 一键打包

在**仓库根目录**执行：

**macOS**
```bash
bash ./scripts/pack/build_macos.sh
# 产出: dist/CoPaw.app

CREATE_ZIP=1 bash ./scripts/pack/build_macos.sh   # 同时生成 .zip 与 .dmg
```

**Windows (PowerShell)**
```powershell
./scripts/pack/build_win.ps1
# 产出: dist/CoPaw-Setup-<version>.exe
```

## 从终端启动并查看日志（macOS）

如果双击 .app 会闪退，可以在终端里运行以查看完整报错和日志：

```bash
# 在仓库根目录执行，用打包环境里的 python，避免用到系统 conda（路径按需改）
./dist/CoPaw.app/Contents/Resources/env/bin/python -m copaw.cli.main desktop
```

所有标准输出和错误（包括 Python traceback）都会打在终端里；可加 `--log-level debug` 查看更详细日志。

## CI

`.github/workflows/desktop-release.yml`：

- **触发**: Release 发布 或 手动 workflow_dispatch
- **Windows**: 构建 console → 临时 conda 环境 + conda-pack → NSIS → 上传 artifact
- **macOS**: 构建 console → 临时 conda 环境 + conda-pack → .app → zip → 上传 artifact
- **Release**: 若由 release 触发，则把 Windows 安装包与 macOS zip 上传到该 Release 的附件

## 脚本说明

| 文件 | 说明 |
|------|------|
| `build_common.py` | 创建临时 conda 环境、`pip install .`、conda-pack，产出归档；供 macOS/Windows 脚本调用 |
| `build_macos.sh` | 一键：构建 console → build_common → 解压到 CoPaw.app；可选打 zip |
| `build_win.ps1` | 一键：构建 console → build_common → 解压 → 桌面启动 bat → makensis 安装包 |
| `copaw_desktop.nsi` | NSIS 脚本：从 `dist/win-unpacked` 打包并创建快捷方式 |
| `gen_icon_icns.py` | (仅 macOS) 从 `assets/icon.svg`（圆角透明）生成 `icon.icns` |
