# 主题自定义完整指南

本文档详细说明如何自定义CSS主题，创建专属的微信公众号文章样式。

---

## 1. 主题文件结构

### 1.1 主题文件位置

```
wechat-article-formatter/
└── templates/
    ├── tech-theme.css        # 科技风主题
    ├── minimal-theme.css     # 简约风主题
    ├── business-theme.css    # 商务风主题
    └── custom-theme.css      # 你的自定义主题
```

### 1.2 主题文件基本结构

```css
/*
 * 主题名称 - 主题说明
 * 适用场景：具体场景说明
 * 配色：颜色方案说明
 */

/* ========== CSS变量定义 ========== */
:root {
  --primary-color: #7c3aed;
  --secondary-color: #3b82f6;
  /* ... 更多变量 */
}

/* ========== 基础样式 ========== */
body { /* body样式 */ }

/* ========== 标题样式 ========== */
h1, h2, h3 { /* 标题样式 */ }

/* ========== 段落和文本 ========== */
p, strong, em { /* 文本样式 */ }

/* ========== 代码块 ========== */
code, pre { /* 代码样式 */ }

/* ========== 其他元素 ========== */
blockquote, table, img, etc.

/* ========== 响应式优化 ========== */
@media (max-width: 768px) { /* 移动端样式 */ }
```

---

## 2. CSS变量系统

### 2.1 核心变量说明

**颜色变量**:
```css
:root {
  /* 主色调 - 用于标题、链接、强调元素 */
  --primary-color: #7c3aed;

  /* 辅助色 - 用于装饰、渐变 */
  --secondary-color: #3b82f6;

  /* 文字颜色 */
  --text-color: #333333;          /* 正文颜色 */
  --text-light: #666666;          /* 浅色文字（注释、说明） */

  /* 背景颜色 */
  --background: #ffffff;          /* 页面背景 */
  --code-bg: #282c34;             /* 代码块背景 */
  --quote-bg: #f8f5ff;            /* 引用块背景 */

  /* 边框颜色 */
  --quote-border: #7c3aed;        /* 引用块边框 */
  --border-radius: 8px;           /* 圆角半径 */
}
```

**为什么使用CSS变量？**
1. **统一管理**: 所有颜色在一处定义
2. **易于修改**: 修改一次，全局生效
3. **语义化**: 变量名清晰表达用途
4. **可复用**: 在多个地方使用同一变量

### 2.2 如何使用CSS变量

**定义变量**:
```css
:root {
  --my-color: #7c3aed;
}
```

**使用变量**:
```css
h1 {
  color: var(--primary-color);
  border-left: 4px solid var(--primary-color);
}
```

**带备选值**:
```css
/* 如果--primary-color未定义，使用#7c3aed */
h1 {
  color: var(--primary-color, #7c3aed);
}
```

### 2.3 完整变量列表

```css
:root {
  /* === 颜色系统 === */
  --primary-color: #7c3aed;           /* 主色 */
  --secondary-color: #3b82f6;         /* 辅色 */
  --accent-color: #10b981;            /* 强调色 */

  /* === 文字颜色 === */
  --text-color: #333333;              /* 正文 */
  --text-light: #666666;              /* 浅色 */
  --text-dark: #1a1a1a;               /* 深色（标题） */
  --text-muted: #999999;              /* 灰色（次要信息） */

  /* === 背景颜色 === */
  --background: #ffffff;              /* 页面背景 */
  --background-alt: #f8f9fa;          /* 交替背景 */

  /* === 代码相关 === */
  --code-bg: #282c34;                 /* 代码块背景 */
  --code-color: #abb2bf;              /* 代码文字 */
  --inline-code-bg: #f5f5f5;          /* 行内代码背景 */
  --inline-code-color: #e83e8c;       /* 行内代码颜色 */

  /* === 引用块 === */
  --quote-bg: #f8f5ff;                /* 引用背景 */
  --quote-border: #7c3aed;            /* 引用边框 */

  /* === 表格 === */
  --table-header-bg: #7c3aed;         /* 表头背景 */
  --table-border: #dee2e6;            /* 表格边框 */
  --table-stripe-bg: #f8f9fa;         /* 斑马纹背景 */

  /* === 尺寸 === */
  --border-radius: 8px;               /* 圆角 */
  --spacing-unit: 8px;                /* 间距单位 */
  --max-width: 720px;                 /* 最大宽度 */

  /* === 字体 === */
  --font-base: 16px;                  /* 基础字号 */
  --font-h1: 28px;                    /* H1字号 */
  --font-h2: 24px;                    /* H2字号 */
  --font-h3: 20px;                    /* H3字号 */
  --line-height: 1.8;                 /* 行高 */
}
```

---

## 3. 创建自定义主题

### 3.1 方法A: 修改现有主题

**步骤1: 复制现有主题**
```bash
cd templates/
cp tech-theme.css my-custom-theme.css
```

**步骤2: 修改CSS变量**
```css
:root {
  /* 修改主色调为绿色 */
  --primary-color: #10b981;      /* 原: #7c3aed */
  --secondary-color: #14b8a6;    /* 原: #3b82f6 */

  /* 修改代码块背景为浅色 */
  --code-bg: #f5f5f5;            /* 原: #282c34 */
  --code-color: #333333;         /* 原: #abb2bf */
}
```

**步骤3: 测试主题**
```bash
python scripts/markdown_to_html.py \
  --input test.md \
  --theme my-custom \
  --preview
```

**注意**: 主题名称是CSS文件名去掉 `-theme.css` 后缀。例如：
- `my-custom-theme.css` → 主题名: `my-custom`
- `dark-theme.css` → 主题名: `dark`

### 3.2 方法B: 从头创建主题

**步骤1: 创建新的CSS文件**
```bash
touch templates/dark-theme.css
```

**步骤2: 使用主题模板**
```css
/*
 * Dark Theme - 深色主题
 * 适用场景：科技、编程、极客内容
 * 配色：深灰黑色，高对比
 */

:root {
  /* 深色主题配色 */
  --primary-color: #60a5fa;        /* 亮蓝色 */
  --secondary-color: #a78bfa;      /* 亮紫色 */
  --text-color: #e5e7eb;           /* 浅灰文字 */
  --text-light: #9ca3af;           /* 更浅的灰色 */
  --background: #1f2937;           /* 深灰背景 */
  --code-bg: #111827;              /* 接近黑色 */
  --code-color: #f3f4f6;           /* 浅色代码 */
  --quote-border: #60a5fa;
  --quote-bg: #374151;
  --border-radius: 8px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont,
    "Segoe UI", Roboto, "Helvetica Neue", Arial,
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    sans-serif;
  font-size: 16px;
  line-height: 1.8;
  color: var(--text-color);
  background: var(--background);
  padding: 20px;
  max-width: 720px;
  margin: 0 auto;
}

/* 继续添加其他样式... */
```

**步骤3: 复制必要的样式**

从现有主题复制以下部分：
1. 标题样式（h1, h2, h3）
2. 段落和文本（p, strong, em）
3. 代码块（code, pre）
4. 引用块（blockquote）
5. 列表（ul, ol）
6. 表格（table）
7. 图片（img）
8. 链接（a）
9. 分隔线（hr）
10. 响应式样式（@media）

### 3.3 主题测试清单

创建主题后，测试以下要素：

- [ ] **标题**: H1/H2/H3样式清晰，层级分明
- [ ] **段落**: 字体大小合适，行高舒适
- [ ] **代码块**: 背景和文字对比度足够
- [ ] **表格**: 表头突出，数据易读
- [ ] **引用块**: 与正文区分明显
- [ ] **列表**: 标记清晰，缩进正确
- [ ] **图片**: 居中显示，间距合适
- [ ] **链接**: 颜色与正文区分
- [ ] **移动端**: 在手机上显示正常

---

## 4. 主题配色方案

### 4.1 科技/现代风格

**配色方案1: 蓝紫渐变（tech主题）**
```css
:root {
  --primary-color: #7c3aed;      /* 紫色 */
  --secondary-color: #3b82f6;    /* 蓝色 */
  --accent-color: #06b6d4;       /* 青色 */
}
```

**配色方案2: 蓝绿科技**
```css
:root {
  --primary-color: #0891b2;      /* 蓝绿色 */
  --secondary-color: #10b981;    /* 绿色 */
  --accent-color: #14b8a6;       /* 青色 */
}
```

**配色方案3: 橙紫对比**
```css
:root {
  --primary-color: #f97316;      /* 橙色 */
  --secondary-color: #a855f7;    /* 紫色 */
  --accent-color: #ec4899;       /* 粉色 */
}
```

### 4.2 简约/文艺风格

**配色方案4: 黑白灰（minimal主题）**
```css
:root {
  --primary-color: #333333;      /* 深灰 */
  --secondary-color: #666666;    /* 中灰 */
  --text-color: #333333;
  --background: #ffffff;
}
```

**配色方案5: 温暖米色**
```css
:root {
  --primary-color: #92400e;      /* 棕色 */
  --secondary-color: #b45309;    /* 浅棕 */
  --background: #fffbeb;         /* 米色 */
  --text-color: #1c1917;
}
```

### 4.3 商务/专业风格

**配色方案6: 深蓝金色（business主题）**
```css
:root {
  --primary-color: #1e3a8a;      /* 深蓝 */
  --secondary-color: #f59e0b;    /* 金色 */
  --accent-color: #dc2626;       /* 红色（强调） */
}
```

**配色方案7: 墨绿商务**
```css
:root {
  --primary-color: #065f46;      /* 墨绿 */
  --secondary-color: #047857;    /* 绿色 */
  --accent-color: #ca8a04;       /* 金色 */
}
```

### 4.4 配色工具推荐

- **Coolors.co**: 配色方案生成器
- **Adobe Color**: 专业配色工具
- **Material Design Colors**: Google配色指南
- **Flat UI Colors**: 扁平化配色

---

## 5. 样式定制详解

### 5.1 标题样式定制

**H1标题样式示例**:

```css
/* 样式1: 左侧渐变边框 */
h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 32px 0 24px 0;
  padding-left: 16px;
  border-left: 4px solid var(--primary-color);
  position: relative;
}

h1::before {
  content: "";
  position: absolute;
  left: -4px;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%);
}

/* 样式2: 底部渐变下划线 */
h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-color);
  margin: 32px 0 24px 0;
  padding-bottom: 16px;
  border-bottom: 3px solid var(--secondary-color);
}

/* 样式3: 居中带装饰 */
h1 {
  font-size: 28px;
  font-weight: 700;
  color: #000;
  margin: 32px 0 24px 0;
  text-align: center;
  position: relative;
}

h1::after {
  content: "";
  display: block;
  width: 60px;
  height: 3px;
  background: var(--primary-color);
  margin: 12px auto 0;
}
```

**H2标题样式示例**:

```css
/* 样式1: 左侧边框 */
h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 28px 0 20px 0;
  padding-left: 12px;
  border-left: 4px solid var(--secondary-color);
}

/* 样式2: 底部部分下划线 */
h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 28px 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid transparent;
  background-image: linear-gradient(90deg,
    var(--primary-color) 0%,
    var(--secondary-color) 50%,
    transparent 50%);
  background-size: 100% 2px;
  background-position: 0 100%;
  background-repeat: no-repeat;
}

/* 样式3: 带序号 */
h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 28px 0 20px 0;
  counter-increment: h2-counter;
}

h2::before {
  content: counter(h2-counter) ". ";
  color: var(--primary-color);
  font-weight: 700;
}
```

### 5.2 代码块样式定制

**浅色代码块**:
```css
pre {
  background: #f5f5f5;
  color: #333333;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e1e4e8;
  overflow-x: auto;
  margin: 20px 0;
  line-height: 1.6;
}

pre code {
  background: transparent;
  color: inherit;
  font-size: 14px;
  font-family: "SFMono-Regular", Consolas, monospace;
}
```

**深色代码块（Atom One Dark）**:
```css
pre {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 20px 0;
}

/* 语法高亮 */
.hljs-keyword { color: #c678dd; }  /* 关键字-紫色 */
.hljs-string { color: #98c379; }   /* 字符串-绿色 */
.hljs-function { color: #61afef; } /* 函数-蓝色 */
.hljs-number { color: #d19a66; }   /* 数字-橙色 */
.hljs-comment { color: #5c6370; }  /* 注释-灰色 */
```

**代码块添加语言标签**:
```css
pre::before {
  content: attr(data-lang);
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 12px;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 1px;
}
```

### 5.3 表格样式定制

**渐变表头**:
```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

table thead {
  background: linear-gradient(135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%);
  color: #ffffff;
}

table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
}

table td {
  padding: 12px 16px;
  border: 1px solid #dee2e6;
}

table tbody tr:nth-child(even) {
  background: #f8f9fa;
}

table tbody tr:hover {
  background: #f1f3f5;
}
```

**简约表格**:
```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

table th {
  padding: 12px 16px;
  background: #f6f8fa;
  border: 1px solid #ddd;
  font-weight: 600;
}

table td {
  padding: 12px 16px;
  border: 1px solid #ddd;
}

table tbody tr:nth-child(even) {
  background: #fafafa;
}
```

### 5.4 引用块样式定制

**彩色左边框**:
```css
blockquote {
  margin: 20px 0;
  padding: 16px 20px;
  background: var(--quote-bg);
  border-left: 4px solid var(--quote-border);
  border-radius: 0 8px 8px 0;
  color: var(--text-light);
  font-style: italic;
}
```

**带图标引用**:
```css
blockquote {
  margin: 20px 0;
  padding: 16px 20px 16px 60px;
  background: #f8f5ff;
  border-left: 4px solid #7c3aed;
  position: relative;
}

blockquote::before {
  content: "💡";
  position: absolute;
  left: 20px;
  top: 16px;
  font-size: 24px;
}
```

**卡片式引用**:
```css
blockquote {
  margin: 20px 0;
  padding: 20px;
  background: #ffffff;
  border: 2px solid var(--primary-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

---

## 6. 响应式设计

### 6.1 移动端优化

**基础响应式**:
```css
@media (max-width: 768px) {
  body {
    padding: 16px;
    font-size: 15px;
  }

  h1 { font-size: 24px; }
  h2 { font-size: 20px; }
  h3 { font-size: 18px; }

  pre {
    padding: 12px;
    font-size: 13px;
  }

  table {
    font-size: 14px;
  }

  table th, table td {
    padding: 8px 10px;
  }
}
```

### 6.2 响应式断点

```css
/* 小屏手机 */
@media (max-width: 480px) {
  body { font-size: 14px; }
  h1 { font-size: 22px; }
}

/* 大屏手机/小平板 */
@media (min-width: 481px) and (max-width: 768px) {
  body { font-size: 15px; }
  h1 { font-size: 24px; }
}

/* 平板/小屏桌面 */
@media (min-width: 769px) and (max-width: 1024px) {
  body { font-size: 16px; }
  h1 { font-size: 26px; }
}

/* 桌面 */
@media (min-width: 1025px) {
  body { font-size: 16px; }
  h1 { font-size: 28px; }
}
```

---

## 7. 高级技巧

### 7.1 使用CSS Grid布局

```css
.two-column-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 768px) {
  .two-column-layout {
    grid-template-columns: 1fr;
  }
}
```

### 7.2 自定义列表样式

```css
ul li {
  list-style-type: none;
  position: relative;
  padding-left: 24px;
}

ul li::before {
  content: "▸";
  position: absolute;
  left: 0;
  color: var(--primary-color);
  font-weight: 600;
}
```

### 7.3 添加提示框样式

```css
.tip {
  padding: 16px 20px;
  margin: 20px 0;
  background: #e7f5ff;
  border-left: 4px solid #3b82f6;
  border-radius: 0 8px 8px 0;
}

.warning {
  background: #fff3cd;
  border-color: #ffc107;
}

.danger {
  background: #fee;
  border-color: #dc3545;
}
```

---

## 8. 主题发布

### 8.1 主题命名规范

- 使用小写字母和连字符
- 格式: `name-theme.css`
- 示例: `dark-theme.css`, `ocean-theme.css`

### 8.2 主题文档

在主题CSS文件顶部添加注释：

```css
/*
 * Ocean Theme - 海洋主题
 * 作者: Your Name
 * 版本: 1.0.0
 * 适用场景: 清新、自然、环保类内容
 * 配色: 蓝绿海洋色系
 *
 * 主要特点:
 * - 清新的蓝绿配色
 * - 流畅的渐变效果
 * - 适合科普、自然类文章
 *
 * 使用方法:
 * python scripts/markdown_to_html.py --theme ocean
 */
```

### 8.3 分享主题

1. 确保主题CSS文件完整
2. 测试所有样式元素
3. 提供示例文章
4. 分享主题文件和截图

---

## 9. 故障排除

### Q1: CSS变量不生效？

**检查**:
- 变量是否在 `:root` 中定义
- 使用 `var()` 函数时是否拼写正确
- 浏览器是否支持CSS变量

### Q2: 样式在微信中丢失？

**原因**: CSS变量无法内联

**解决**: 转换脚本会自动替换CSS变量为实际值

### Q3: 渐变效果不显示？

**检查**:
- 渐变语法是否正确
- 是否提供了备选颜色
- 部分旧设备可能不支持复杂渐变

---

## 10. 参考资源

- [CSS Variables (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [CSS Grid (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout)
- [Coolors.co](https://coolors.co/) - 配色工具
- [Google Fonts](https://fonts.google.com/) - 字体参考
