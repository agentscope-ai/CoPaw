---
name: wechat_formatter
description: "将 Markdown 文章转换为美化的 HTML 格式，适配微信公众号发布。应用专业 CSS 样式、代码高亮、优化排版。当用户说'美化这篇文章'、'转换为HTML'、'优化公众号格式'、'生成公众号HTML'时使用。"
author: 智语观潮
homepage: https://github.com/BND-1/wechat_article_skills
metadata:
  {
    "copaw":
      {
        "emoji": "🎨",
        "requires": {}
      }
  }
---

# 微信公众号文章格式化工具

**目标**：将 Markdown 文章转换为适配微信公众号的精美 HTML，实现一键发布。

---

## 执行流程

### 步骤1：获取输入文件

**场景判断**：

| 场景 | 如何处理 |
|------|---------|
| 用户提供文件路径 | 直接使用该路径 |
| 用户粘贴 Markdown 内容 | 先使用 write_file 保存为 .md 文件 |
| 刚使用过 wechat_writer | 自动查找最新生成的 .md 文件 |
| 用户只说"美化文章" | 询问用户：文件路径或粘贴内容 |

**自动检测最新文章**（与 wechat_writer 集成）：
```bash
latest_md=$(ls -t *.md 2>/dev/null | head -1)
if [ -n "$latest_md" ]; then
    echo "检测到最新文章：$latest_md"
fi
```

---

### 步骤2：检查 examples 目录（优先使用精美模板）

**重要规则**：
1. **优先使用 examples 中的精美模板**，而非基础 CSS 主题
2. **不要渲染 H1 标题**：微信公众号有独立的标题输入框，HTML 中不应包含文章标题

**检查可用模板**：

使用 `execute_shell_command` 列出模板：
```bash
ls -lh {skill_dir}/examples/
```

其中 `{skill_dir}` 为本 skill 所在目录。

**可用模板**：

| 模板文件 | 风格特色 | 适用场景 |
|---------|---------|---------|
| **VSCode 蓝色科技风.html** | 导语块、序号章节标题、功能卡片、操作步骤 | 技术文章、产品介绍、教程 |
| **红蓝对决 深度测评模板.html** | 渐变标题、对比卡片、数据表格、引用金句 | 对比评测、深度分析 |
| **极客暗黑风.html** | 深色背景、极客风格 | 技术深度文章 |
| **现代极简风.html** | 简约清爽 | 通用文章 |

**选择逻辑**：
- 技术/产品介绍类 -> VSCode 蓝色科技风
- 对比/评测类 -> 红蓝对决模板
- 深度技术文章 -> 极客暗黑风
- 通用内容 -> 现代极简风

**执行方式**：
1. 使用 `read_file` 读取选中的模板文件
2. 参照模板的组件结构（导语块、卡片、步骤列表等）
3. **跳过 Markdown 中的 H1 标题**，从第一个段落或 H2 开始
4. 手动将 Markdown 内容映射到模板组件中
5. 在 HTML 开头添加注释：`<!-- 标题请在微信公众号编辑器中单独填写 -->`
6. **转换代码块格式**：
   使用 `execute_shell_command` 运行：
   ```bash
   python {skill_dir}/scripts/convert-code-blocks.py input.html output.html
   ```
7. 生成精美的 HTML 文件

**如果没有合适的模板**，才使用步骤3的基础 CSS 主题转换。

---

### 步骤3：选择基础主题（仅当 examples 无合适模板时使用）

**决策树**（自动选择或询问用户）：
- 包含代码块或技术词汇多 -> tech（科技风）
- 包含数据表格、商业术语 -> business（商务风）
- 纯文字、通用内容 -> minimal（简约风）

**主题对照表**：

| 主题 | 适用场景 | 配色 |
|------|---------|------|
| **tech** | 技术文章、AI、编程教程 | 蓝紫渐变 |
| **minimal** | 生活随笔、读书笔记 | 黑白灰 |
| **business** | 商业报告、数据分析 | 深蓝金 |

---

### 步骤4：执行转换

使用 `execute_shell_command` 运行：
```bash
python {skill_dir}/scripts/markdown_to_html.py \
  --input "{文件路径}" \
  --theme {主题名} \
  --output "{输出路径}" \
  --preview
```

其中 `{skill_dir}` 为本 skill 所在目录。

**参数说明**：
- `--input`：Markdown 文件路径（必需）
- `--theme`：tech / minimal / business（默认 tech）
- `--output`：HTML 输出路径（可选，默认同名 .html）
- `--preview`：转换后自动在浏览器打开预览（推荐）

---

### 步骤5：质量检查

转换完成后，使用 `read_file` 读取生成的 HTML 文件（前 50 行），检查：

| 检查项 | 如何验证 | 常见问题 |
|-------|---------|---------|
| 标题样式 | 查看 `<h1>`, `<h2>` 标签的 style 属性 | 样式丢失则重新转换 |
| 代码高亮 | 查看 `<pre><code>` 是否有语言标识 | 无高亮则检查 Markdown 是否指定语言 |
| 图片路径 | 查看 `<img src="">` 的路径 | 本地路径需提醒用户上传到微信 |
| 表格格式 | 查看 `<table>` 是否有内联样式 | 格式混乱则简化表格列数 |

---

### 步骤6：预览和反馈

询问用户预览效果是否满意：
- 满意 -> 进入发布步骤（可使用 wechat_publisher）
- 不满意 -> 切换主题或手动修复

**常见调整**：

| 问题 | 解决方案 |
|------|---------|
| "颜色不喜欢" | 切换主题重新生成 |
| "代码块没高亮" | 检查 Markdown 代码块是否指定语言 |
| "图片显示不正常" | 本地图片需上传到微信编辑器 |
| "表格太宽" | 简化表格或接受横向滚动 |

---

### 步骤7：发布指导

输出给用户的完整指导：

1. 打开微信公众号编辑器
2. 在标题栏填写文章标题
3. 打开生成的 HTML 文件
4. 在浏览器中按 Ctrl+A（全选） -> Ctrl+C（复制）
5. 粘贴到编辑器正文区（Ctrl+V）
6. 处理图片：删除无法显示的本地图片引用，重新上传图片到微信编辑器
7. 使用微信编辑器的"预览"功能在手机查看
8. 确认无误后发布

注意事项：
- 样式已内联，可直接粘贴
- 本地图片需重新上传
- 粘贴后微信编辑器可能微调部分样式（正常）

---

## 与 wechat_writer 集成

**识别标志**：用户刚说过"写一篇关于XXX的文章"，当前目录有新生成的 .md 文件

**无缝衔接话术**：
```
检测到你刚用 wechat_writer 生成了文章：{文件名}
现在为你美化格式，使用 tech 主题...
```

---

## 错误处理

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `FileNotFoundError` | 文件路径错误 | 询问用户正确的文件路径 |
| `Unknown theme` | 主题名错误 | 提示可用主题：tech/minimal/business |
| 转换成功但代码无高亮 | 未指定语言 | 提醒用户修改代码块 |
| 图片无法显示 | 本地路径或外链失效 | 提醒在微信编辑器重新上传 |

---

## 常用命令

**标准转换**：
```bash
python {skill_dir}/scripts/markdown_to_html.py --input article.md --theme tech --preview
```

**批量转换**：
```bash
python {skill_dir}/scripts/batch_convert.py --input articles/ --theme minimal --workers 8
```

**实时预览**：
```bash
python {skill_dir}/scripts/preview_generator.py --input article.md --theme business
```

---

## 参考文档

- `references/publishing-guide.md` - 详细发布步骤
- `references/theme-customization.md` - 主题自定义指南
- `references/wechat-constraints.md` - 微信平台限制说明
- `references/wechat-code-blocks.md` - 代码块处理说明
