<p align="center">
  <img src="https://raw.githubusercontent.com/agentscope-ai/CloudPaw/main/docs/cloudpaw.png" alt="CloudPaw" width="360" />
</p>

<p align="center">
  <strong>AI-Powered Alibaba Cloud Assistant Plugin for QwenPaw</strong>
</p>

<p align="center">
  <a href="https://github.com/agentscope-ai/CloudPaw/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python" /></a>
  <a href="#"><img src="https://img.shields.io/badge/version-0.0.1-green.svg" alt="Version" /></a>
</p>

<p align="center">
  <b>English</b> | <a href="README_zh.md">中文</a>
</p>

---

CloudPaw is an Alibaba Cloud AI assistant plugin for QwenPaw, combining **QwenPaw + Aliyun CLI** with deep **ROS (Resource Orchestration Service)** integration. It's not just a chatbot — it's an intelligent assistant with a cloud-native execution engine.

Simply describe your needs in natural language, and CloudPaw will automate the entire process from resource creation to application deployment. For example:

- **One-sentence app deployment**: Tell CloudPaw "Help me build a personal website" — it will automatically create an ECS instance, configure security groups, deploy the application, and return an accessible URL.
- **Quick personal site launch**: Describe the content and style you want, and CloudPaw generates the code, deploys to the cloud, and binds a public endpoint.
- **Rapid API service publishing**: Specify your interface definitions, and CloudPaw handles the full pipeline from code generation and container building to service exposure.

CloudPaw runs entirely in your own environment, keeping your data secure and under your control.

## Quick Start

### Prerequisites

| Item | Requirement |
|------|-------------|
| **QwenPaw version** | **≥ v1.1.7** |
| **Python** | 3.10 ~ 3.13 |
| **Alibaba Cloud account** | Access Key required for cloud operations |

> For QwenPaw installation, see [QwenPaw Quickstart](https://qwenpaw.agentscope.io/docs/quickstart). If your QwenPaw version is below v1.1.7, upgrade first: `pip install --upgrade qwenpaw>=1.1.7`.

### 1. Install CloudPaw Plugin

CloudPaw is pre-bundled with QwenPaw v1.1.7+ at `plugins/bundle/cloudpaw/`.

**Via Console (recommended):**

1. Launch QwenPaw (`qwenpaw app`), open http://127.0.0.1:8088/
2. Click **"Plugin Manager"** in the left sidebar (under Settings) → **"Install Plugin"**
3. Enter the path to the `cloudpaw/` folder, or drag it into the dialog
4. Wait for installation to complete

**Via CLI:**

```bash
qwenpaw plugin install /path/to/cloudpaw
```

> ⚠️ After installation, you **must refresh the browser** (`Ctrl+Shift+R` / `Cmd+Shift+R`) to load frontend updates.

### 2. Configure

After installing CloudPaw, complete these configurations:

#### ① QwenPaw Model

Configure an LLM provider and API Key in console **Settings → Models**. See [QwenPaw Models docs](https://qwenpaw.agentscope.io/docs/models).

#### ② Alibaba Cloud Credentials

Configure in console **"Environment Variables"** (CloudPaw auto-creates placeholder entries):

- `ALIBABA_CLOUD_ACCESS_KEY_ID` — your Access Key ID
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET` — your Access Key Secret
- `ALIBABA_CLOUD_REGION_ID` — region ID (defaults to `cn-hangzhou`)

You can also configure via system environment variables or CLI. For instructions on obtaining Access Keys, refer to the [Alibaba Cloud documentation](https://help.aliyun.com/document_detail/116401.html). We recommend using a primary account Access Key with full permissions.

#### ③ iac-code Model

CloudPaw relies on [iac-code](https://github.com/aliyun/iac-code) for IaC template generation. Run `iac-code` in your terminal for first-time guided setup, or manually edit `~/.iac-code/settings.yml`.

### 3. Start Using

Select **"CloudPaw-Master"** from the agent dropdown in the chat page to start.

> **⚠️ Risk Warning: Please Read Before Use**
>
> 1. **Resource Risk**: This service requires Alibaba Cloud admin credentials with full account access. Operations may create, modify, or delete resources in your account.
> 2. **Security Advice**: Proceed with caution and monitor your existing resources. **Back up important data** before use, and regularly check resource status and billing.
> 3. **Disclaimer**: This service is fully AI-driven. AI may produce errors or inaccurate results. You are responsible for reviewing and confirming AI operations and bear responsibility for the final outcomes. We are not liable for any losses caused by AI operations.
> 4. **Cost Notice**: Cloud resource creation and usage will incur corresponding cloud service fees. Please monitor your billing and plan resource usage accordingly.

## Architecture

CloudPaw integrates via the QwenPaw native plugin system without modifying QwenPaw's core code.

```
QwenPaw/
└── plugins/
    └── bundle/
        └── cloudpaw/           # CloudPaw plugin (frontend & backend)
            ├── plugin.json     # Plugin manifest
            ├── plugin.py       # Backend entry point
            ├── requirements.txt # Python dependencies (iac-code, httpx-sse)
            ├── ui/             # Frontend plugin (custom tool call renderers)
            ├── skills/         # Skill definitions
            ├── tools/          # Tool implementations
            ├── modules/        # Modules
            ├── agents/         # Agent prompts and configurations
            └── prompts/        # Prompt definitions
```

## Features

- **ROS Deployment Orchestration**: Automate Alibaba Cloud resource deployment via [iac-code](https://github.com/aliyun/iac-code) engine for ROS/Terraform template generation
- **Resource Proposal Selection**: Interactive multi-proposal comparison and selection with dedicated frontend rendering (`proposal_choice` tool)
- **PRD Management Frontend Enhancement**: Custom frontend rendering for QwenPaw Mission Mode's PRD management (`manage_prd` tool)
- **Multi-Agent Collaboration**: Orchestrate multiple agents for complex deployment tasks via QwenPaw Mission Mode
- **Auto-dependency Setup**: Automatically installs `iac-code` and Alibaba Cloud CLI during plugin startup

## Multi-Agent Architecture

CloudPaw implements multi-agent collaboration via QwenPaw's **Mission Mode**. Users interact with the master agent, which automatically breaks down requirements into a PRD (Product Requirements Document) and delegates tasks to specialized sub-agents by story priority.

| Agent | Responsibility |
|---|---|
| **CloudPaw-Master** | Orchestration: user dialogue, requirement clarification, PRD generation, task delegation, result aggregation |
| **CloudPaw-Executor** | General execution: code writing, app deployment, environment configuration, CLI operations |
| **CloudPaw-Verifier** | Unified verification: cloud resource status, app functionality, accessibility, security compliance |
| **iac-code** (External ACP Agent) | IaC engine: invoked asynchronously via ACP protocol for ROS/Terraform template generation, cost estimation, and stack management |

## Usage Examples

**Deploy a personal homepage to the cloud**

> Help me create a personal homepage and deploy it to the cloud. The page should include: personal introduction, skills, project experience, and contact info — please use placeholders for all personal information. The style should be clean and minimal, responsive for mobile and desktop. Please deploy using Alibaba Cloud ECS.

**Quickly publish an API service to the cloud**

> Help me quickly deploy an API service to the cloud. I want it to provide /health and /hello endpoints by default, and give me a callable URL with example requests. Keep the configuration as simple and clean as possible.
