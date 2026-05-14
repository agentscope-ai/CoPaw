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

> **Note**: Starting from QwenPaw v1.1.7, CloudPaw is bundled inside the QwenPaw repository at `plugins/bundle/cloudpaw/`. Users can install it directly from the QwenPaw console's **Plugin Manager** — no separate clone or install script needed.

CloudPaw is an Alibaba Cloud AI assistant plugin for [QwenPaw](https://github.com/agentscope-ai/QwenPaw), combining **QwenPaw + Aliyun CLI** with deep **ROS (Resource Orchestration Service)** integration. It's not just a chatbot — it's an intelligent assistant with a cloud-native execution engine.

Simply describe your needs in natural language, and CloudPaw will automate the entire process from resource creation to application deployment. For example:

- **One-sentence app deployment**: Tell CloudPaw "Help me build a personal website" — it will automatically create an ECS instance, configure security groups, deploy the application, and return an accessible URL.
- **Instant personal site launch**: Describe the content and style you want, and CloudPaw generates the code, deploys to the cloud, and binds a public endpoint.
- **Rapid API service publishing**: Specify your interface definitions, and CloudPaw handles the full pipeline from code generation and container building to service exposure.

CloudPaw runs entirely in your own environment, keeping your data secure and under your control.

## Quick Start

### 1. Install QwenPaw (v1.1.7+)

```bash
pip install qwenpaw>=1.1.7
```

Verify installation:

```bash
qwenpaw --version
```

### 2. Launch QwenPaw

```bash
qwenpaw app
```

Open your browser at http://localhost:8088.

### 3. Install CloudPaw Plugin

1. In the QwenPaw console, click **"Plugin Manager"** in the left sidebar (under Settings).
2. Click **"Install Plugin"**.
3. Select the `cloudpaw` folder from `plugins/bundle/cloudpaw/` inside the QwenPaw installation directory, or drag it into the install dialog.
4. Wait for the installation to complete.

> CloudPaw is pre-bundled with QwenPaw v1.1.7+. After installation, select "CloudPaw-Master" from the agent dropdown in the top-left corner to start using it.

### 4. Configure Alibaba Cloud Credentials

> **⚠️ Important**: CloudPaw requires Alibaba Cloud Access Keys to perform cloud resource operations. You must configure credentials before using CloudPaw.

#### Option A: Configure via QwenPaw Console (Recommended)

CloudPaw automatically creates the following placeholder entries in QwenPaw's "Environment Variables" settings after launch:

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `ALIBABA_CLOUD_REGION_ID` (defaults to `cn-hangzhou`)

Open QwenPaw Console → "Environment Variables" in the left sidebar → fill in the values and save. Credentials are encrypted and stored locally, accessible only within the QwenPaw process.

#### Option B: Configure via System Environment Variables

If you prefer to set credentials before launching, you can configure them via system environment variables:

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIBABA_CLOUD_REGION_ID="cn-hangzhou"  # Optional, defaults to cn-hangzhou
```

> If these keys are already set in your system environment, CloudPaw will not override them.

For instructions on obtaining Access Keys, refer to the [Alibaba Cloud documentation](https://help.aliyun.com/document_detail/116401.html). We recommend using a primary account Access Key with full permissions to avoid restrictions on resource creation and deployment.

> **⚠️ Risk Warning: Please Read Before Use**
>
> 1. **Resource Risk**: This service requires Alibaba Cloud admin credentials with full account access. Operations may create, modify, or delete resources in your account.
> 2. **Security Advice**: Proceed with caution and monitor your existing resources. **Back up important data** before use, and regularly check resource status and billing.
> 3. **Disclaimer**: This service is fully AI-driven. AI may produce errors or inaccurate results. You are responsible for reviewing and confirming AI operations and bear responsibility for the final outcomes. We are not liable for any losses caused by AI operations.
> 4. **Cost Notice**: Cloud resource creation and usage will incur corresponding cloud service fees. Please monitor your billing and plan resource usage accordingly.

After configuring credentials, you can start using CloudPaw.

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

- **ROS Deployment Orchestration**: Automate Alibaba Cloud resource deployment via ROS templates
- **Resource Proposal Selection**: Interactive multi-proposal comparison and selection (`proposal_choice` tool)
- **ROS Cost Estimation**: Real-time ROS template cost estimation (`ros_plan_builder` tool)
- **PRD Management**: Auto-generate and manage Product Requirements Documents (`manage_prd` tool)
- **Multi-Agent Collaboration**: Orchestrate multiple agents for complex deployment tasks via QwenPaw Mission Mode
- **Custom Frontend Rendering**: Dedicated UI components for `proposal_choice`, `ros_plan_builder`, and `manage_prd` tools
- **Auto-dependency Setup**: Automatically installs `iac-code` and Alibaba Cloud CLI during plugin startup

## Multi-Agent Architecture

CloudPaw implements multi-agent collaboration via QwenPaw's **Mission Mode**. Users interact with the master agent, which automatically breaks down requirements into a PRD (Product Requirements Document) and delegates tasks to specialized sub-agents by story priority.

| Agent | Responsibility |
|---|---|
| **CloudPaw-Master** | Orchestration: user dialogue, requirement clarification, PRD generation, task delegation, result aggregation |
| **CloudPaw-Executor** | General execution: code writing, app deployment, environment configuration, CLI operations |
| **CloudPaw-Verifier** | Unified verification: cloud resource status, app functionality, accessibility, security compliance |

**Workflow:**

1. User describes requirements → CloudPaw-Master clarifies and generates PRD
2. PRD is split into stories, delegated in parallel by priority to corresponding sub-agents
3. Each story is automatically verified by CloudPaw-Verifier upon completion
4. All stories pass → results are aggregated and returned to the user

## Usage Examples

**Deploy a personal homepage to the cloud**

> Help me create a personal homepage and deploy it to the cloud. The page should include: personal introduction, skills, project experience, and contact info — please use placeholders for all personal information. The style should be clean and minimal, responsive for mobile and desktop. Please deploy using Alibaba Cloud ECS.

**Quickly publish an API service to the cloud**

> Help me quickly deploy an API service to the cloud. I want it to provide /health and /hello endpoints by default, and give me a callable URL with example requests. Keep the configuration as simple and clean as possible.

## License

This project is licensed under the [Apache License 2.0](LICENSE), consistent with QwenPaw.
