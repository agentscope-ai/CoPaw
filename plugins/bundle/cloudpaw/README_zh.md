<p align="center">
  <img src="https://raw.githubusercontent.com/agentscope-ai/CloudPaw/main/docs/cloudpaw.png" alt="CloudPaw" width="360" />
</p>

<p align="center">
  <strong>QwenPaw 的阿里云AI助手插件</strong>
</p>

<p align="center">
  <a href="https://github.com/agentscope-ai/CloudPaw/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python" /></a>
  <a href="#"><img src="https://img.shields.io/badge/version-0.0.1-green.svg" alt="Version" /></a>
</p>

<p align="center">
  <a href="README.md">English</a> | <b>中文</b>
</p>

---

> **说明**：从 QwenPaw v1.1.7 起，CloudPaw 已内置在 QwenPaw 仓库的 `plugins/bundle/cloudpaw/` 目录中。用户可以通过 QwenPaw 控制台的**「插件管理」**直接安装，无需单独克隆仓库或运行安装脚本。

CloudPaw 是 [QwenPaw](https://github.com/agentscope-ai/QwenPaw) 的阿里云AI助手插件，融合 **QwenPaw + Aliyun CLI** 两大核心组件，并深度集成 **ROS（资源编排）** 能力——它不是简单的聊天机器人，而是一个具备云原生执行引擎的智能助手。

只需用自然语言描述你的需求，CloudPaw 就能自动完成从资源创建到应用部署的全流程。例如：

- **一句话搭建应用**：告诉 CloudPaw "帮我搭建一个个人网站"，它会自动创建 ECS 实例、配置安全组、部署应用并返回可访问的地址。
- **个人站点秒级上线**：描述你想要的页面内容和风格，CloudPaw 自动生成代码、部署到云端、绑定公网访问。
- **API 服务快速发布**：指定接口定义，CloudPaw 完成从代码生成、容器构建到服务暴露的整个链路。

CloudPaw 完全部署在您自己的环境中，数据安全可控。

## 快速开始

### 1. 安装 QwenPaw（v1.1.7+）

```bash
pip install qwenpaw>=1.1.7
```

安装后验证：

```bash
qwenpaw --version
```

### 2. 启动 QwenPaw

```bash
qwenpaw app
```

打开浏览器访问 http://localhost:8088 。

### 3. 安装 CloudPaw 插件

1. 在 QwenPaw 控制台中，点击左侧导航栏的**「插件管理」**（设置分组下）。
2. 点击**「安装插件」**按钮。
3. 在 QwenPaw 安装目录的 `plugins/bundle/cloudpaw/` 中选择 `cloudpaw` 文件夹，或将其拖拽到安装对话框中。
4. 等待安装完成。

> CloudPaw 已预置在 QwenPaw v1.1.7+ 中。安装完成后，在左上角的 Agent 下拉框中选择「CloudPaw-Master」即可开始使用。

### 4. 配置阿里云凭证

> **⚠️ 重要**：CloudPaw 需要阿里云 Access Key 才能正常执行云资源操作，使用前必须完成凭证配置。

#### 方式 A：在 QwenPaw 控制台配置（推荐）

CloudPaw 启动后会自动在 QwenPaw 的「环境变量」设置中创建以下占位条目：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `ALIBABA_CLOUD_REGION_ID`（默认 `cn-hangzhou`）

打开 QwenPaw 控制台 → 左侧导航栏「环境变量」 → 填入对应的值并保存即可。该方式下凭证会加密存储在本地，且仅在 QwenPaw 进程内可用。

#### 方式 B：通过系统环境变量配置

如果你希望在启动前就完成配置，也可以通过系统环境变量设置：

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIBABA_CLOUD_REGION_ID="cn-hangzhou"  # 可选，默认 cn-hangzhou
```

> 如果系统环境变量中已配置了上述 Key，CloudPaw 不会覆盖，优先使用系统中的值。

Access Key 的获取方式请参考[阿里云官方文档](https://help.aliyun.com/document_detail/116401.html)。建议使用具有完整权限的主账号 Access Key，以确保资源创建、部署等操作不受权限限制。

> **⚠️ 风险提示：请在使用前仔细阅读**
>
> 1. **资源风险警告**：本服务需要使用阿里云管理员凭证，该凭证具有完整的账户访问权限。继续操作可能会对您阿里云账户中的现有资源产生影响，包括创建、修改或删除资源。
> 2. **安全建议**：请务必谨慎操作，并对您账户中的现有资源保持监控。建议在使用前**备份重要数据**，并定期检查资源状态和费用账单。
> 3. **免责声明**：本服务全过程由 AI 驱动，AI 可能会产生错误或不准确的结果。您需要对 AI 执行的操作进行审核和确认，并对最终结果负责。我们不对 AI 操作导致的任何损失承担责任。
> 4. **费用说明**：使用本服务过程中，如果涉及云资源的创建或使用，将会产生相应的云服务费用。请关注您的账单并合理规划资源使用。

完成凭证配置后即可开始使用 CloudPaw。

## 架构

CloudPaw 通过 QwenPaw 原生插件系统接入，不修改 QwenPaw 核心代码。

```
QwenPaw/
└── plugins/
    └── bundle/
        └── cloudpaw/           # CloudPaw 插件（前后端）
            ├── plugin.json     # 插件清单
            ├── plugin.py       # 后端入口
            ├── requirements.txt # Python 依赖（iac-code, httpx-sse）
            ├── ui/             # 前端插件（自定义 tool call 渲染）
            ├── skills/         # 技能定义
            ├── tools/          # 工具实现
            ├── modules/        # 模块
            ├── agents/         # Agent prompt 和配置
            └── prompts/        # Prompt 定义
```

## 功能

- **ROS 部署编排**：通过 ROS 模板自动化阿里云资源部署
- **资源方案选择**：交互式多方案对比和选择（`proposal_choice` 工具）
- **ROS 询价**：实时 ROS 模板成本估算（`ros_plan_builder` 工具）
- **PRD 管理**：自动生成和管理产品需求文档（`manage_prd` 工具）
- **多 Agent 协作**：基于 QwenPaw Mission Mode 编排多个 Agent 协同完成复杂部署任务
- **前端自定义渲染**：`proposal_choice`、`ros_plan_builder` 和 `manage_prd` 工具的专属 UI 组件
- **自动依赖安装**：插件启动时自动安装 `iac-code` 和阿里云 CLI

## 多 Agent 协作架构

CloudPaw 基于 QwenPaw 的 **Mission Mode** 实现多 Agent 协作。用户只需与主控 Agent 对话，系统会自动将需求拆解为 PRD（产品需求文档），再按 Story 粒度委派给各专业子 Agent 执行。

| Agent | 职责 |
|---|---|
| **CloudPaw-Master** | 主控编排：用户对话、需求澄清、生成 PRD、委派任务、汇总结果 |
| **CloudPaw-Executor** | 通用执行：代码编写、应用部署、环境配置、CLI 操作 |
| **CloudPaw-Verifier** | 统一验证：云资源状态、应用功能、访问性、安全合规 |

**工作流程：**

1. 用户描述需求 → CloudPaw-Master 澄清并生成 PRD
2. PRD 拆分为多个 Story，按优先级并行委派给对应子 Agent
3. 每个 Story 完成后自动派发 CloudPaw-Verifier 验证
4. 所有 Story 通过后汇总结果返回用户

## 使用示例

**创建个人主页并部署到云端**

> 帮我创建一个个人主页并上线到云端。页面包含：个人介绍、技能展示、项目经历、联系方式，所有个人信息请先用占位符代替。风格简洁清爽，适配手机和电脑。请使用阿里云 ECS 部署。

**快速发布 API 服务到云端**

> 帮我把一个 API 服务快速发布到云端。我希望默认提供 /health 和 /hello 两个接口，并给我可直接调用的地址和示例请求，配置尽量简单清晰。

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源，与 QwenPaw 保持一致。
