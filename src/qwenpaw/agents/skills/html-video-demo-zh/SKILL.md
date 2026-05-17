---
name: html-video-demo
description: 构建单文件 HTML "视频演示"——脚本化的 UI 动画时间线，从头到尾如同引导式产品演练或故事模式落地页那样自动播放。沉淀了适用于多种场景（手机锁屏、插件浮层、生产力应用、创意工具、仪表盘、终端）的通用模式：场景注册表、轴线 HUD、工作区素材激活、流水线阶段卡、卡内状态机、文字打字辅助、自动滚动、用于点击模拟的光标、氛围主题、SVG 插图、Web Audio 音效、重置模式。当用户需要交互式 HTML 演练、落地页内嵌演示，或是无需后端和构建步骤、可在浏览器中直接播放的故事模式"看它如何工作"页面时，使用此技能。可选通过 audio-narration 参考文档添加自动对齐画面的语音旁白；可选通过 video-export 参考文档导出带片头与背景音乐的 MP4。
metadata:
  builtin_skill_version: "1.0"
---

# 带脚本化 UI 编排的单文件 HTML 演示

"视频演示"是一个 HTML 文件，播放起来像引导式产品巡览：GSAP 时间线上的脚本化 UI 动画、人物切换器、播控控件和故事地图。观看者点播放就开始看；可以暂停、拖动进度条、切换人物，也可以让它自动跑完。本技能沉淀了在六个差异巨大的场景（锁屏、插件浮层、生产力应用、创意工具、轻量仪表盘、终端）中都站得住的模式——架构、可复用的组件模式，以及只有真正发布过才会知道的坑。

## 何时使用本技能

- 你想做一个**产品演练或"故事模式"**，以单个自包含 HTML 文件播放
- 页面具有**基于时间轴的 UI 编排**（GSAP、Anime.js、CSS 动画或手写 JS）
- 你**不是在做视频**——你想要的是一个真正可交互的 HTML 页面，观看者可以拖动进度条、暂停、在场景间切换、检查元素
- 用户希望分享单个 URL 或文件，而不是上传视频
- 可选：叠加 **TTS 语音旁白**，画面自动对齐——见 `references/audio-narration.md`。（可跳过；HTML 模式本身已能独立成立。）

## 技术栈

挑可用的最小集合：

- **GSAP**（CDN）——时间线 + 补间 + 回调
- **Tailwind**（CDN play 脚本）——用于外框和布局的工具类。组件形态的样式自带 CSS。
- **Google Fonts**——Inter + JetBrains Mono 是非常稳的默认组合
- **内联 SVG** 用于所有插图 / 图标
- **Web Audio API** 用于一次性音效（手机震动、提示音）——别引整套音频库

不需要构建步骤。整个演示就是一个 `.html` 文件加一个 `assets/` 目录。

## 顶层架构

一个 `scenes` 注册表。每个场景是一个普通 JS 对象：

```js
const scenes = {
  intro: {
    sceneEnd: 28.0,
    transportLabel: 'Product · Intro',
    closingSvg: './assets/story-intro.svg',
    closingCaption: 'Strong closing line.',
    closingSub:     'Subtext that names what just happened.',
    stageMood: 'night',                // optional theming
    beats: [                           // drives the right-rail story map
      { t: 0.0,  clk: '08:00', label: 'Idle',         hud: 'Setup state.' },
      { t: 1.5,  clk: '08:01', label: 'First action', hud: 'Axis · what fires.' },
      // ...
    ],
    reset() { /* return all elements to t=0 visual state */ },
    buildTimeline() { /* return a paused GSAP timeline */ },
  },
  // ... more scenes
};
```

单一的 `loadScene(id)` 函数负责编排：

1. 杀掉前一个时间线（`prevTl.pause(); prevTl.kill()`）
2. 给新场景的 `<section>` 设 `data-active="true"`，其他设为 `false`
3. 为新场景重新渲染节拍列表 + 进度条标记
4. 调用 `scene.reset()` 清掉视觉状态
5. 构建新时间线（暂停）
6. 短暂延迟后开始播放

## 每个演示都需要的五个共享元素

| 元素 | 位置 | 用途 |
|---|---|---|
| **场景区块** | 舞台内的 `<section id="scene-{id}" class="scene">` | 装载所有场景专属 HTML 的容器 |
| **右侧栏** | 所有场景共用 | 当前字幕 · 轴线 HUD · 故事地图（节拍列表） |
| **播控条** | 底部栏 | 播放 / 重置 / 进度条 / 静音 / 场景标签 |
| **人物条** | 顶部栏 | 快速场景切换器 |
| **结尾条** | 舞台下方 | 场景结束时滑入的结尾 SVG + 字幕 |

右侧栏和播控条是**共享的**——它们会根据当前激活的场景重新渲染内容。场景区块通过 `data-active` 进行**切换**。

```css
.scene { display: none; }
.scene[data-active="true"] { display: flex; flex-direction: column; align-items: center; }
```

## 节拍系统

`beats: [{ t, clk, label, hud }, ...]` 是故事的骨架。

- `t`（秒，场景时间）——此节拍变为"激活"的时间点
- `clk`——展示给观看者的虚构挂钟字符串（例如 `'03:14:02'`）
- `label`——故事地图和当前节拍字幕的简短标题
- `hud`——显示在轴线详情行的较长句子；这里要写清楚*哪个轴 / 系统组件在做什么*

时间线的 `onUpdate` 调用单个 `syncMeta(t)` 函数来判断当前节拍：

```js
function syncMeta(t) {
  const beats = scenes[activeSceneId].beats;
  let idx = 0;
  for (let i = 0; i < beats.length; i++) if (t >= beats[i].t) idx = i;
  // update beat list rows (data-state="done"/"active"/"pending")
  // update caption-time, caption-text, axis-detail
  // update time-elapsed and scrubber
}
```

每行节拍的状态完全由 `data-state` 属性驱动——剩下的交给 CSS。没有任何针对单元素的 JS 状态。

## 轴线 HUD 模式

右侧栏顶部有一排 N 个"轴线胶囊"（5 个是不错的数量，但按你架构的实际定义来用）。每个胶囊有三种视觉状态：

- **空闲**：低饱和度颜色
- **激活**：脉冲、强调色、轻微放大
- **已触发**：持续的暗色，表示在本场景中曾被使用

```css
.axis-pill[data-active="true"] {
  color: #fff;
  box-shadow: 0 0 24px var(--accent), 0 0 0 1px var(--accent) inset;
  background: color-mix(in oklab, var(--accent) 16%, transparent);
}
.axis-pill[data-fired="true"]:not([data-active="true"]) {
  color: color-mix(in oklab, var(--accent) 70%, #94a3b8);
}
```

从时间线调用的 `pulseAxis(name, holdSec)` 辅助函数：

```js
function pulseAxis(name, hold = 1.2) {
  const pill = axisPills[name];
  pill.dataset.active = 'true';
  pill.dataset.fired  = 'true';
  gsap.fromTo(pill, { scale: 1 }, { scale: 1.08, duration: 0.16, yoyo: true, repeat: 1 });
  clearTimeout(pill._holdTimer);
  pill._holdTimer = setTimeout(() => { pill.dataset.active = 'false'; }, hold * 1000);
}

// inside buildTimeline:
tl.call(() => pulseAxis('skills', 4.0), null, 6.5);  // pulse for 4s at scene_t=6.5
```

这一个视觉元素做了很多工作——它是观看者在观看演示时学习架构词汇的方式。把它和节拍中的 `hud` 字符串配套使用（点名同一条轴线，比如 "Skills · pulling X"），词汇就在每个节拍里被强化两次。

## 表面多样性：每种人物用不同的窗口模式

不要让每个场景都复用相同的窗口外框。表面应该看起来像那个人物实际工作的世界：

| 人物原型 | 表面 | 美学要点 |
|---|---|---|
| On-call 运维 | 手机锁屏 | 深色壁纸、灵动岛、堆叠通知卡 |
| 企业 IM 用户 | 聊天应用插件（浮层） | 浅色主题、侧边面板、宿主应用品牌可见 |
| 知识工作者（中文） | 生产力 wiki（语雀风） | 柔和边框、宽松内边距、带文件夹的侧边栏 |
| 创意专业人士 | 专业工具（DaVinci 风） | 深色、等宽字体文件名、彩色评分 |
| 数据分析师 | 浅色收件箱 / 仪表盘 | Outlook 风调色板、图表作为产物 |
| 对冲基金 / 交易员 | Bloomberg 风终端 | 纯黑、琥珀色等宽字体、信息密集 |

对每种表面，决定：
- **窗口尺寸**（920×580 是不错的默认值）
- **配色方案**（最多 3–4 种颜色加单一强调色）
- **字体**——正文 sans + 等宽；展示中文时加 CJK 回退（`PingFang SC`）
- **macOS 风红绿灯**（`<span class="r"><span class="y"><span class="g">`）以极低成本传达"这是一个应用窗口"
- **窗口内部工具栏**带品牌标识 + 路径 / 标题

## 工作区素材激活模式

当演示中的"智能体"读取 N 个资料源时，把它们作为侧栏列表展示出来，并**随每个被读取而点亮**：

```html
<div class="ws-asset" data-asset="brand-kit" data-state="waiting">
  <span class="ws-asset-icon">🎨</span>
  <div>
    <div class="ws-asset-name">brand-kit</div>
    <div class="ws-asset-sub">palette · type · logo</div>
  </div>
  <span class="ws-asset-check"></span>  <!-- ○ → ● (amber pulsing) → ✓ -->
</div>
```

```css
.ws-asset { opacity: 0.5; transition: opacity 250ms, transform 250ms; }
.ws-asset[data-state="active"] { opacity: 1; transform: translateX(2px); }
.ws-asset[data-state="done"]   { opacity: 1; }
.ws-asset[data-state="active"] .ws-asset-check {
  background: #f59e0b;
  animation: pulse-amber 1.2s ease-in-out infinite;
}
.ws-asset[data-state="done"] .ws-asset-check { background: #34d399; }
.ws-asset[data-state="done"] .ws-asset-check::after { /* draw a small ✓ */ }
```

由时间线驱动：

```js
function setAsset(id, state, at) {
  tl.call(() => {
    document.querySelector(`.ws-asset[data-asset="${id}"]`).dataset.state = state;
  }, null, at);
}

setAsset('brand-kit', 'active', 8.5);
setAsset('product',   'active', 8.6);
setAsset('brand-kit', 'done',  10.5);
setAsset('product',   'done',  10.6);
```

这一个模式让"智能体使用*这些具体文件*"变得可见——没有它，生成看上去像魔法。

## 流水线阶段卡

对于多阶段流程（SQL → 图表 → 叙述；pdf-parse → diff → synthesize → translate），使用层叠卡片，在 `waiting → active → done` 之间脉冲推进：

```html
<div class="stage" data-state="waiting">
  <div class="stage-head">
    <span class="stage-num">STAGE 1</span>
    <span class="stage-title">Title</span>
    <div class="stage-chips">
      <span class="stage-chip skl">SKL</span>
      <span class="stage-chip net">NET</span>
    </div>
    <span class="stage-status">waiting</span>
  </div>
  <div class="stage-body"><!-- action lines, mini progress bar, ticks --></div>
</div>
```

```css
.stage { opacity: 0.42; transition: opacity 350ms, border-color 350ms, box-shadow 350ms; }
.stage[data-state="active"] {
  opacity: 1;
  border-color: rgba(251,191,36,0.30);
  box-shadow: 0 0 22px rgba(251,191,36,0.08);
}
.stage[data-state="done"] {
  opacity: 1;
  border-color: rgba(52,211,153,0.22);
}
```

每个阶段卡可承载自己的可视化——SQL 语法高亮、迷你条形图、z-score 阈值用的横向"扫描"条。装饰可自由发挥；保持外层状态机一致即可。

## 单卡内部的状态机

有时单个 UI 元素需要经历多个阶段——比如一个通知卡走 diagnosing → hypothesis-with-buttons → executing → resolved；或一个生成卡走 queued → generating（闪光）→ still（图）→ animating → animated（带 Ken Burns 效果和播放角标的图）。

模式：一个外层元素带 `data-stage` 属性，多个内层块依据 stage 显示 / 隐藏：

```html
<div class="card" data-stage="queued">
  <div class="card-preview">
    <div class="placeholder-grid"></div>
    <div class="scene-img-bg"></div>
    <div class="shimmer"></div>
    <span class="play-badge">▶</span>
  </div>
  <div class="card-body">…</div>
</div>
```

```css
.card[data-stage="generating"] .shimmer    { opacity: 1; }
.card[data-stage="still"]      .scene-img-bg { opacity: 1; }
.card[data-stage="animated"]   .scene-img-bg { animation: ken-burns 4s ease-in-out infinite alternate; }
.card[data-stage="animated"]   .play-badge   { opacity: 1; }
```

可逆性提示：通过 `.call()` 设置的 `data-attribute` 变化只在前向触发。如果向后拖动进度条需要"撤销"某个 stage，请用 `gsap.set` 和反向 set 成对处理，或干脆接受只支持前向拖动这一现实。

## 文字打字辅助函数

对于长文本逐字出现——只需一个辅助函数：

```js
function typeInto(selector, text, t0, t1, charsPerStep = 4) {
  const steps = Math.ceil(text.length / charsPerStep);
  const dur = (t1 - t0) / steps;
  for (let i = 0; i < steps; i++) {
    const upTo = Math.min(text.length, (i + 1) * charsPerStep);
    tl.set(selector, { textContent: text.slice(0, upTo) }, t0 + i * dur);
  }
}

typeInto('#draft', '一段长文本…', 10.5, 14.0, 3);
```

`gsap.set(..., { textContent: '...' })` 可以正常工作——GSAP 会直接给属性赋值。每一步占用一个补间槽位，但成本很低。

中文文本用更小的 `charsPerStep`（2–3）；拉丁字母用 4–5 读起来更自然。

## 内容增长面板的自动滚动

当一个面板不断追加内容（逐字录入的文档、滚动日志、增长的流水线列表）时，要滚动以保持最新内容可见：

```js
function scrollToBottom(panelSelector, at) {
  tl.call(() => {
    const p = document.querySelector(panelSelector);
    if (p) gsap.to(p, { scrollTop: p.scrollHeight, duration: 0.45, ease: 'power2.out' });
  }, null, at);
}

scrollToBottom('#doc-panel', 10.5);
scrollToBottom('#doc-panel', 12.3);
```

CSS：在面板上设 `overflow-y: auto; scroll-behavior: smooth;`。

聊天消息这类最新消息始终停在底部的场景，替代方案：`display: flex; flex-direction: column; justify-content: flex-end; overflow: hidden;` ——内容自动贴底，溢出从顶部裁掉。

## 用于点击模拟的光标

一个小型浮动元素，动画移动到目标位置以模拟点击：

```html
<div class="tap-cursor"></div>
```

```css
.tap-cursor {
  position: absolute;
  width: 30px; height: 30px;
  border-radius: 50%;
  background: radial-gradient(circle at center, rgba(255,255,255,0.45) 0%, rgba(255,255,255,0.10) 50%, transparent 70%);
  border: 1.5px solid rgba(255,255,255,0.85);
  opacity: 0;
  z-index: 40;
  transform: translate(-50%, -50%);
}
```

在时间线中：

```js
// approach a button
tl.set('#tap-cursor', { left: '30%', top: '95%', opacity: 0, scale: 1 }, 16.0)
  .to('#tap-cursor', { opacity: 1, duration: 0.3 }, 16.0)
  .to('#tap-cursor', { left: '74%', top: '87%', duration: 0.9, ease: 'power2.inOut' }, 16.1)
// tap (pulse the cursor + the target)
  .to('#tap-cursor', { scale: 0.55, duration: 0.12, yoyo: true, repeat: 1 }, 17.0)
  .to('#approve-btn', { backgroundColor: '#16a34a', duration: 0.2 }, 17.1)
// retreat
  .to('#tap-cursor', { opacity: 0, duration: 0.4 }, 17.4);
```

`transform: translate(-50%, -50%)` 让 `left:74%; top:87%;` 表示"光标*中心*落在那个位置"。GSAP 仍可以对光标进行 scale，因为 scale 与居中 transform 是组合关系。

相对于已知容器（通常是窗口或舞台）来定位。百分比坐标可用，不需要像素级对齐。

## 场景氛围 / 主题

通过单一属性进行每场景的氛围调整：

```html
<main id="stage-bg" data-mood="night">…</main>
```

```css
#stage-bg[data-mood="night"]   { background: linear-gradient(180deg, #0b1124, #060914); }
#stage-bg[data-mood="morning"]::before {
  content: '';
  position: absolute; inset: 0;
  pointer-events: none;
  background:
    radial-gradient(45% 35% at 88% 8%, rgba(253, 186, 116, 0.10), transparent 55%),
    radial-gradient(40% 30% at 6% 92%, rgba(196, 132, 252, 0.06), transparent 55%);
}
```

`loadScene()` 设置 mood：
```js
document.getElementById('stage-bg').dataset.mood = scenes[id].stageMood;
```

细微但有效，让凌晨 3 点的场景与周一清晨的场景区分开，而无需重做整个窗口美学。

## 用 SVG 插图作为场景预览

当演示引用尚不存在的"视频"或"图片"时，内联 data-URI SVG 能以极低成本撑起这种错觉：

```css
.scene-img.coffee-shot {
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 50' preserveAspectRatio='xMidYMid slice'><rect width='80' height='50' fill='%23451a03'/><ellipse cx='40' cy='32' rx='22' ry='5' fill='%231c1917'/><!-- … --></svg>");
  background-size: cover;
  background-position: center;
}
```

内联 SVG-in-CSS 规则：
- data URI 内 HTML 属性用 `'`（单引号）；外层用 `"`
- 把 `#` 进行 URL 编码为 `%23`（颜色值、`url(#gradId)` 引用）
- 用 `<defs>` + 渐变以低成本增加深度
- 80×50 viewBox 在竖向 / 方形 / 横向比例下都能良好切片
- 4–6 个彩色形状足以暗示一个场景；别想画照片

同一张插图可以同时作为剪辑缩略图（40×24）、侧栏图标（44×26）、渲染预览（24×40）和主视觉（320×180）——`preserveAspectRatio="xMidYMid slice"` 全都能搞定。

## 用 Web Audio 做一次性音效

不要打包一整套音效库。要做一段短促音效（手机震动、提示音、按钮点击），直接合成：

```js
let audioCtx = null;
function getCtx() {
  if (audioCtx) return audioCtx;
  const AC = window.AudioContext || window.webkitAudioContext;
  audioCtx = new AC();
  return audioCtx;
}

function playBuzz() {
  const ctx = getCtx();
  if (ctx.state !== 'running') return;     // wait for user gesture
  const now = ctx.currentTime;
  // two short pulses with tremolo, low-pass filtered
  for (const t0 of [now, now + 0.24]) {
    const o1 = ctx.createOscillator(); o1.type = 'sawtooth'; o1.frequency.value = 130;
    const o2 = ctx.createOscillator(); o2.type = 'square';   o2.frequency.value = 136;
    const trem = ctx.createOscillator(); trem.type = 'sine'; trem.frequency.value = 46;
    const tremDepth = ctx.createGain(); tremDepth.gain.value = 0.45;
    trem.connect(tremDepth);
    const filt = ctx.createBiquadFilter(); filt.type = 'lowpass'; filt.frequency.value = 720;
    const env = ctx.createGain();
    env.gain.setValueAtTime(0, t0);
    env.gain.linearRampToValueAtTime(0.20, t0 + 0.008);
    env.gain.linearRampToValueAtTime(0.12, t0 + 0.12);
    env.gain.exponentialRampToValueAtTime(0.001, t0 + 0.22);
    o1.connect(filt); o2.connect(filt);
    filt.connect(env);
    tremDepth.connect(env.gain);
    env.connect(ctx.destination);
    [o1, o2, trem].forEach(n => { n.start(t0); n.stop(t0 + 0.24); });
  }
}
```

在任何用户手势上预激活 AudioContext（否则因为自动播放策略 `playBuzz` 不出声）：

```js
['click', 'keydown', 'touchstart'].forEach(ev =>
  window.addEventListener(ev, () => {
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  }, { passive: true })
);
```

## 重置模式

每个场景都需要一个 `reset()` 将其恢复到 t=0 状态。它在时间线从头播放前运行（首次加载和重新开始）。

需要显式重置的内容（任何被时间线*改动过*的东西）：
- 元素的 opacity、transform、自定义 CSS 属性
- `data-state`、`data-stage`、`data-active` 属性
- 任何被时间线写入的元素的 `textContent`
- 动态创建的子节点（清空 `innerHTML`）
- 光标位置
- 结尾条的 opacity + transform

```js
reset() {
  gsap.set(['#card-1', '#card-2', '#card-3'], { opacity: 0, y: -12 });
  document.querySelectorAll('.ws-asset').forEach(el => el.dataset.state = 'waiting');
  document.getElementById('output-list').innerHTML = '';
  gsap.set('#closing-strip', { opacity: 0, y: 20 });
  // ...
}
```

场景的 `reset()` 通常会膨胀到 20–40 行。这没问题。替代方案——让时间线通过反向播放自然恢复一切——更脆弱。

## 常见坑点

**GSAP `tl.set({}, { textContent: '...' })`** 是可用的，但只对真实 DOM 元素生效，不支持类 jQuery 的集合。始终传单个选择器字符串或单个 Element。

**`overflow: hidden` + `position: absolute` 的子元素**没问题——但如果你想让绝对定位的子元素相对容器定位，容器要设 `position: relative`。常见 bug：光标锚到了 `body` 上，因为容器忘了写 `position: relative`。

**Tailwind CDN 的 MutationObserver** 会捕获动态插入的 DOM，所以 `innerHTML = '<div class="bg-red-500">...'` 是可用的。但动态内容的首次绘制可能短暂闪过无样式。对演示节奏来说通常不可见；如果你介意，就把那个 class 写到普通 CSS 里。

**同一时间对同一属性多次 `tl.set()`**——最后一个生效。适合写"该元素初始隐藏且偏移 y=-12"而不用单独写 `gsap.set` 设置初始状态。

**如果你从外部时钟（如音频旁白）驱动时间线，必须用 `gsap.timeline({ paused: true })`**。否则时间线会自动播放并与你的 seek 调用打架。

**结尾条动画的相互干扰**——结尾条是所有场景共用的（同一个 DOM 元素，每个场景都把 `opacity` 重置为 0）。中途切换场景时，先杀掉前一个时间线以防过时补间还在动它。

**`gsap.to(el, { className: '+=foo' })`** 支持类操作，但跨 GSAP 版本表现脆弱。优先在 `.call()` 里用普通的 `el.classList.add(...)`；或者更好——用 CSS 选择器驱动的 `data-state` 属性。

**人物条的"激活"高亮**应该在每次 `loadScene()` 时重置。别依赖旧的激活状态做视觉以外的任何事。

## 单文件打包

演示应当双击即可打开——无需服务器。

- 所有 CSS 内联在 `<style>` 中
- 所有 JS 内联在 `<script>` 中
- 音频 + SVG 插图作为相对路径 `./assets/...` 引用（浏览器 `file://` 可用）
- GSAP 和 Tailwind 各一个 CDN script 标签；Google Fonts 一个 `<link>`

如果你需要*真正*离线可移植的单文件：
- 内联 GSAP 源码（~70 KB）
- 内联 Tailwind 静态构建（`tailwindcss` CLI 构建，purge 后 ~10 KB）
- 把音频嵌为 data URI（仅在总量 < 5 MB 时；否则保持外部）
- 场景 SVG 同样内嵌（上面已经做了）

对普通演示而言，CDN + 相对资源的做法已经足够，文件也更可读。

## 添加语音旁白（可选）

加一段 TTS 配音，**即便你之后再改脚本，仍保持与画面对齐**——音频成为主时钟，GSAP 时间线自动 seek 跟随。这套模式用 OpenAI TTS 或阿里 DashScope 的 Qwen-TTS 合成（脚本根据环境中存在哪个 API key 来挑选；两个都在就询问），Whisper 出时间戳，每个场景配一小组 `[audioTime, sceneTime]` "锚点"。

各部件位于 `scripts/`（TTS 生成、Whisper 转录、时间戳导出），完整流程 + HTML 接线方式记录在 **`references/audio-narration.md`** 中。给场景加音频前先读那个。

快速心智模型：
- 把旁白写成普通 `.txt` 文件（每个场景一份）
- `generate-tts.py` → 每场景一份 mp3
- `transcribe.py` → 每场景的词级时间戳
- `dump-timestamps.py` → 短语级美化输出，便于挑选锚点时刻
- 给每个场景配置加 `checkpoints: [[audioT, sceneT], ...]`
- 一个 `requestAnimationFrame` 循环读 `audio.currentTime`，在锚点之间插值，并调用 `timeline.time(sceneT)` ——非均匀节奏自然出现

## 导出为 MP4（可选）

当用户希望得到一个可分享的视频时，可以把演示导出成单个 MP4，带片头 + 环境音乐——无需把它重写成视频框架的合成格式（HyperFrames、Remotion 等）。流水线是 Playwright + CDP screencast 出视频，Python + ffmpeg `adelay`/`amix` 出音频，全部由磁盘上已有的每场景 mp3 驱动。

关键想法：GSAP 时间线由 `audio.currentTime` 驱动，因此抓取无头浏览器的画面输出、再按抓到的 `audio-play` 时刻拼接相同的音频文件，就能得到帧级精准同步——根本不用录桌面音频。

该模式要求演示实现一个小的 `?clean=1` 模式（隐藏外框、强制串联所有场景、把标记发到 `window.__movieMarks`、结束时设 `__movieDone`）。完整流程、clean 模式的 CSS+JS 骨架、片头模板、画质旋钮（`--dpr 2` 是最大的单一画质杠杆）、音频同步校正、以及坑点（宽泛子选择器命中兄弟元素、grain SVG 分辨率、ARM64 Chromium、CJK 字体可用性、编码器 pix_fmt 不匹配）都记录在 **`references/video-export.md`** 中。

快速心智模型：
- 在演示中实现 clean 模式契约（即插即用的 CSS + JS 块——见参考文档）
- `record-html-movie.py --demo demo.html --out demo.mp4 --dpr 2 --crf 16 --preset slow` → 以 2× 抓帧，再用 Lanczos 下采样到 1080p，得到 Retina 画质
- 自定义 `scripts/title.html`（文字 + 颜色），再 `record-html-movie.py --url title.html --audio-track title-music.wav --out title.mp4` —— 或干脆把片头场景直接放进演示的场景注册表，跳过 concat
- `build-title-music.sh` 通过 ffmpeg 正弦叠加合成环境垫底音
- `concat-clips.py title.mp4 demo.mp4 --out final.mp4 --crf 16 --preset slow` 用交叉淡化拼接（只在片头是独立片段时需要）

## 浏览器内观看模式（可选，与视频导出互补）

同一份 HTML 也可以成为一个精致的"端到端像视频一样观看"的页面，在任何现代浏览器中直接看——不需要录制。三处叠加调整即可：

- `body[data-immersive="true"]` 隐藏右侧栏，把舞台扩展为居中的单列
- 故事地图的节拍文字从右侧栏移到**进度条标记的 hover 提示框**中，并在进度条上方加一个微型"now-playing"字幕
- 一个浮动按钮（以及 **F** 键）折叠顶部栏 + 底部栏；当鼠标靠近上/下边缘时，边缘揭示处理器会临时滑出它们

这能在页面内交付与 MP4 相同的 UX——可拖动进度条、可完整查看 DOM。这些模式以及两态（"已提交"+ "瞬时显出"）外框切换逻辑记录在 `references/video-export.md` 中。

## 本技能内的文件

- `scripts/generate-tts.py` ——对每场景 `.txt` 调用 OpenAI Speech API 或 DashScope Qwen-TTS，写出 `.mp3`（按可用 API key 自动选后端；通过 `OPENAI_API_KEY` / `DASHSCOPE_API_KEY` 识别）
- `scripts/transcribe.py` ——对每个 `.mp3` 调用 Whisper，写出词级 `.json`
- `scripts/dump-timestamps.py` ——美化输出短语级转录，便于挑选锚点时间
- `scripts/record-html-movie.py` + `.js` ——把演示录制成 MP4（Playwright + CDP screencast + ffmpeg mux）
- `scripts/title.html` ——片头模板；可编辑 eyebrow / 标题 / 副标题 / 标语 + logo
- `scripts/build-title-music.sh` ——用 ffmpeg 合成一段温暖的 A 小调 9 和弦环境垫底音
- `scripts/concat-clips.py` ——用 `xfade`/`acrossfade` 拼接 MP4 片段
- `references/audio-narration.md` ——完整流程、HTML 接线片段、配音调优、音频专属坑点。**只在**要加旁白时阅读。
- `references/video-export.md` ——MP4 导出完整流程：clean 模式契约、录制器细节、片头 + 音乐、坑点。**只在**要导出视频时阅读。
