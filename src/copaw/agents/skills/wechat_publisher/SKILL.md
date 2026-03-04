---
name: wechat_publisher
description: "自动将 HTML 文章发布到微信公众号草稿箱，支持封面图上传、标题、作者和元数据管理。当用户说'推送到微信'、'发布到公众号草稿'、'上传到草稿箱'或提到微信文章发布时使用。"
homepage: https://github.com/BND-1/wechat_article_skills
metadata:
  {
    "copaw":
      {
        "emoji": "📤",
        "requires": {}
      }
  }
---

# 微信公众号草稿发布器

自动将 HTML 格式的文章发布到微信公众号草稿箱，支持封面图上传、标题、作者和摘要等元数据管理。

## 前置要求（使用前必须检查）

在执行发布任务之前，先确认以下配置：

1. **微信公众号凭证**：需要在 `~/.wechat-publisher/config.json` 中配置 `appid` 和 `appsecret`。
   - 获取方式：登录 https://mp.weixin.qq.com → 设置 → 基本配置
2. **服务器 IP 白名单**：需要将运行 CoPaw 的机器 IP 添加到微信公众号后台的 IP 白名单中。
   - 设置位置：微信公众号后台 → 设置 → 基本配置 → IP 白名单

**首次使用时，请主动检查配置文件是否存在，如不存在则引导用户完成配置。**

---

## 快速开始

使用 `execute_shell_command` 运行：

**最简单的用法**：
```bash
python {skill_dir}/publisher.py --title "文章标题" --content article.html
```

**完整参数**：
```bash
python {skill_dir}/publisher.py \
  --title "标题" \
  --content article.html \
  --author "作者名" \
  --cover cover.png \
  --digest "文章摘要"
```

其中 `{skill_dir}` 为本 skill 所在目录。

## 执行步骤

发布文章到微信草稿箱的完整流程：

1. **查找 HTML 文件**
   - 优先查找 `*_formatted.html`（wechat_formatter 输出）
   - 回退到最新的 `.html` 文件

2. **提取文章标题**
   - 从 HTML 注释提取：`<!-- Title: xxx -->`
   - 从文件名提取
   - 询问用户

3. **检查封面图**
   - 查找 `cover.png`
   - 如缺失则警告但继续发布

4. **调用发布脚本**
   ```bash
   python {skill_dir}/publisher.py --title "xxx" --content xxx.html --cover xxx.png
   ```

5. **验证结果**
   - 确认草稿创建成功
   - 获取草稿 media_id

6. **提示用户**
   - 提供微信后台链接
   - 说明下一步操作

## 配置要求

### 首次使用

工具会在首次运行时引导配置：

1. **获取微信公众号凭证**
   - 访问 https://mp.weixin.qq.com
   - 进入 设置 -> 基本配置
   - 复制 AppID 和 AppSecret

2. **运行发布器**
   ```bash
   python {skill_dir}/publisher.py --title "测试" --content test.html
   ```

3. **添加服务器 IP 到白名单**（如需要）

### 配置文件

**位置**：`~/.wechat-publisher/config.json`

**格式**：
```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_secret_here"
}
```

## 核心功能

- access_token 自动缓存（有效期 7200 秒）
- 封面图上传和管理
- HTML 内容自动优化（适配微信）
- 字段长度自动截断（标题/作者/摘要）
- 错误处理和重试机制
- 中文错误提示和解决方案
- 交互模式和命令行模式

## 工作流集成

与其他 skill 协同工作：

**完整工作流**：
1. `wechat_writer` -> 生成文章（`xxx.md` + `cover.png`）
2. `wechat_formatter` -> 格式化 HTML（`xxx_formatted.html`）
3. `wechat_publisher` -> 发布到微信草稿箱（本 skill）

**自动检测机制**：
- 自动查找 `*_formatted.html` 文件
- 自动查找 `cover.png` 封面图
- 自动识别内容图片

## 常见问题

### 错误：IP 不在白名单
**症状**：`invalid ip not in whitelist`
**解决**：
1. 登录微信公众号后台
2. 进入 设置 -> 基本配置
3. 添加服务器 IP 到白名单

### 错误：AppSecret 错误
**症状**：`AppSecret error`
**解决**：
- 检查配置文件：`~/.wechat-publisher/config.json`
- 验证 AppID 以 "wx" 开头（18 个字符）
- 确认 AppSecret 正确

### 错误：标题/作者超出限制
**症状**：`title/author size out of limit`
**解决**：
- 工具会自动截断（标题：32 字节，作者：20 字节）

## 发布后操作

发布成功后：
1. 登录微信公众号后台
2. 进入"草稿箱"
3. 预览效果
4. 确认后发布

注意事项：
- 草稿保存在微信后台，不会立即发布
- 可以在草稿箱中编辑后再发布
- 封面图会在预览时显示
