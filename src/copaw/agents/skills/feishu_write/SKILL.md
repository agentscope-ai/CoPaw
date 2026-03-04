---
name: feishu-write
description: 当用户需要将本地 Markdown 文件发布到飞书文档时使用。支持写入知识库、我的空间、指定文件夹，自动上传图片和保留代码块格式。用户说"发布到飞书"、"写入飞书文档"、"上传到知识库"时触发。
allowed-tools: Read, Write, Edit, Bash
---

# 飞书文档写入

将本地 Markdown 文件写入飞书文档。

## 使用方式

```bash
python -m scripts.feishu_writer <文件路径> [选项]
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `path` | MD 文件路径 | `./doc.md` |
| `--target, -t` | 目标位置 (space/folder/wiki) | `--target wiki` |
| `--folder-token` | 文件夹 token | `--folder-token fldcnxxxxxx` |
| `--wiki-token` | 知识库 node_token | `--wiki-token FWn9wEcZhixVLrk2z5scBx8DnTe` |

## 示例

```bash
# 写入到默认知识库
python -m scripts.feishu_writer ./doc.md --target wiki

# 写入到指定知识库节点
python -m scripts.feishu_writer ./doc.md --target wiki --wiki-token FWn9wEcZhixVLrk2z5scBx8DnTe

# 写入到我的空间
python -m scripts.feishu_writer ./doc.md --target space

# 写入到指定文件夹
python -m scripts.feishu_writer ./doc.md --target folder --folder-token fldcnxxxxxx
```

## 环境配置

需要在 `.env` 文件中配置：

```
FEISHU_APP_ID=应用ID
FEISHU_APP_SECRET=应用密钥
FEISHU_DEFAULT_WIKI_NODE_TOKEN=默认知识库node_token（可选）
FEISHU_DEFAULT_WIKI_SPACE_ID=默认知识库space_id（可选，可自动查询）
```

## 支持的 Markdown 格式

- 标题 (h1-h9)
- 段落文本
- 加粗、斜体、行内代码
- 代码块（支持语法高亮）
- 有序/无序列表
- 引用块
- 图片（本地图片自动上传）
- 链接
- 分割线
