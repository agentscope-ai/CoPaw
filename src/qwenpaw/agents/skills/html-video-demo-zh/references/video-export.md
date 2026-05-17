# 把 HTML 视频演示导出为 MP4

有时演示需要离开浏览器——做成一段用户可以发到 Slack、邮件或幻灯片
里的视频。本参考覆盖端到端流水线：HTML 中的 clean 模式 → 抓帧 →
音频拼装 → 片头 + 音乐 → 最终 concat。所提到的工具位于本技能的
`scripts/` 中，可直接拷入项目使用。

## 流水线实际做了什么

演示的 GSAP 时间线由 `audio.currentTime` 驱动（音频是主时钟——见
`audio-narration.md`）。这意味着无论浏览器在某一刻*渲染*出什么，都
正好与那一刻播放的音频文件对齐。因此录制就是两条相互独立的流：

1. **视频** —— 一个带 `--mute-audio` 的 Playwright/Chromium 会话端
   到端播完演示，同时 CDP screencast 把 JPEG 帧流式写入磁盘。
2. **音频** —— 浏览器播过的那些每场景 `.mp3` 文件，在 Python 中通过
   `adelay` 拼接，让每段在浏览器实际开始播它的那个时刻起始。

最后再 mux 起来。因为两条流参照同一个音频时钟，帧级精确同步自然就
有了。

我们**不**使用 HyperFrames 或任何要求自有合成格式的 HTML-to-video
框架（例如要求每个动画元素都带 `data-start`/`data-duration` 属
性）。现有演示的音频主时钟模式与那些格式不兼容。下面的流水线建立
在这些框架底层用到的同一组原语上——Puppeteer/Playwright + CDP
screencast + ffmpeg——并尊重演示既有的时间线。

## 演示必须实现的 clean 模式契约

录制器以 `?clean=1` 加载演示。演示要做的是：

1. **隐藏外框**，通过基于 `body[data-clean="true"]` 的 CSS 分支——
   顶部栏、右侧栏、播控、模态框。把舞台扩展到铺满视口。*不要*删
   除外框元素；许多场景会在右侧栏内更新 DOM 节点（`caption-text`、
   `axis-detail`、节拍行），删除它们会抛 null 空指针错误。

2. **强制串联所有场景**，那些通常不会自动推进的也要。多数演示在
   "观看者挑选下一个人物"门口停下；clean 模式里你要给链路打补丁，
   让它一气贯到最后一个场景。

3. **为录制器发出标记。** 在每个 `section.scene` 上挂
   `MutationObserver` 监听 `data-active` 翻转；在每个
   `<audio id="audio-*">` 上挂 `addEventListener('play'`，捕获旁白
   起始的精确时刻。它们都进 `window.__movieMarks = []`。

4. **发出起始和结束信号。** 在第一个场景接好线之后置
   `window.__movieReady = true`（录制器等这个再开 screencast）。最
   后一个场景的音频触发 `ended` 之后置 `window.__movieDone = true`
   （录制器轮询这个以知道何时停）。

完整骨架（粘贴在演示主脚本末尾，启动 `loadScene(...)` 调用之前）：

```js
const URL_PARAMS = new URLSearchParams(location.search);
const CLEAN_MODE = URL_PARAMS.get('clean') === '1';
if (CLEAN_MODE) {
  document.body.dataset.clean = 'true';
  // Patch your SCENE_CHAIN so every scene auto-advances.
  Object.assign(SCENE_CHAIN, { /* persona1: persona2, ... */ });
  window.__movieMarks = [];
  window.__movieDone = false;
  const mo = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'data-active' && m.target.dataset.active === 'true') {
        const id = (m.target.id || '').replace(/^scene-/, '');
        if (!id) continue;
        const t = performance.now() / 1000;
        const last = window.__movieMarks[window.__movieMarks.length - 1];
        if (!last || last.scene !== id) {
          window.__movieMarks.push({ scene: id, t });
          if (id === 'FINAL_SCENE_ID') {     // ← put your last scene id here
            const a = document.getElementById(`audio-${id}`);
            if (a) a.addEventListener('ended', () => {
              window.__movieMarks.push({ scene: '__end__', t: performance.now() / 1000 });
              window.__movieDone = true;
            }, { once: true });
          }
        }
      }
    }
  });
  document.querySelectorAll('section.scene').forEach(s =>
    mo.observe(s, { attributes: true, attributeFilter: ['data-active'] })
  );
  document.querySelectorAll('audio[id^="audio-"]').forEach(a => {
    a.addEventListener('play', () => {
      const id = a.id.replace(/^audio-/, '');
      window.__movieMarks.push({ kind: 'audio-play', scene: id, t: performance.now() / 1000 });
    });
  });
}

loadScene(Object.keys(scenes)[0]);
window.__movieReady = true;
```

配套 CSS（粘贴到演示 `<style>` 末尾附近）：

```css
body[data-clean="true"] > header,
body[data-clean="true"] > footer,
body[data-clean="true"] > main > div > aside { display: none !important; }
body[data-clean="true"] { background: #050810; overflow: hidden !important; min-height: 100vh; }
body[data-clean="true"] #stage-bg { min-height: 100vh; display: flex;
                                    align-items: center; justify-content: center; }
body[data-clean="true"] #stage-bg > div {
  max-width: 1180px !important; width: 1180px !important;
  display: block !important; padding: 24px 32px !important; margin: 0 auto !important;
}
body[data-clean="true"] #stage-bg > div > div:first-child { width: 100% !important; padding-top: 0 !important; }
body[data-clean="true"] .grain { display: none !important; }
```

具体选择器取决于你演示的布局，但原则是通用的：隐藏外框，把舞台区
扩展为 1920×1080 视口内的居中 1180px 列，并关掉 grain 噪点叠层
（低编码码率下它会频闪）。

为什么是 1180px？这是本技能里典型"场景"内容的设计宽度（锁屏、
插件浮层、生产力应用等）。1920×1080 画布上居中列两侧各留约 370px
黑边——对视频构图正合适，且不必调整场景内部尺寸。

## 画质旋钮——一开始就挑对

三个设置对最终视频画质影响极大。在启动漫长的录制之前慎重挑选。

**`--dpr 2`（以 2× 像素密度抓取）。** 单一最大画质杠杆。Playwright
以 viewport×DPR 物理像素渲染页面，CDP screencast 抓的就是这个。编
码时再用 `scale=W:H:flags=lanczos` 缩小。下采样起到抗锯齿作用——
文字和细线呈现出 Retina 显示器渲染的质感。没有 `--dpr 2` 的话，
1080p 输出看起来发软，因为观看者 Retina 显示器上的真实演示*本身*就
有 2× 超采样。要匹配。

**`--quality 88` JPEG screencast，`--crf 16 --preset slow` x264。**
screencast 质量是*源*保真度——CRF 再高也救不回 JPEG 已经丢的。
q=88 是不错的折中；q=92 视觉无损但大约大 15%。x264 编码器上，
`preset slow + crf 16` 是 screencast 内容的甜点：保留细节但不过
头，`crf 14` 会多 30% 体积但感知上不会更好。

**磁盘预算。** `--dpr 2` 和 JPEG q=88 下，1080p 逻辑分辨率
（3840×2160 抓取）的每帧平均约 110 KB。15 分钟演示产出约 5 GB
中间帧。预留 7–8 GB 暂存空间；每次跑完清掉 `/tmp/moviecap_*`。

避开"上 4× DPR 或 `crf 12`"的陷阱。它们会让中间体积翻倍、编码速
度大致减半，而差异在 YouTube/Slack 二次编码后已无法保留。

## 音频同步——音频前置延迟很关键

在实时（交互）播放中，`loadScene()` 等 500 ms 才调用 `audio.play()`，
然后音频在 500 ms 内淡入。淡入会掩盖视觉与旁白之间的间隙——观看
者感觉到的是场景出现时音量上升。

录制视频里，淡入是*缺失*的（我们的音频 mux 用 `adelay` 在抓到的
`audio-play` 标记处投入 mp3，然后立刻全音量播放）。如果实时的
500 ms 延迟仍然存在，音频会在视觉场景出现后约 1 秒突然"砰"地切
入——而在视觉相对静止的场景（标题淡入 + 几条要点列表，从
scene-active 到结束之间没什么动画）上，观看者感觉就是"音频拖在场
景后面"。

修法是把 audio 前置延迟和淡入收紧，**仅在 `?clean=1` 时**——保持
实时行为不变：

```js
const preAudioDelayMs = CLEAN_MODE ? 120 : 500;
const fadeInDur       = CLEAN_MODE ? 0.15 : 0.5;
setTimeout(() => {
  audioFadeIn(currentAudio, fadeInDur).then(...);
}, preAudioDelayMs);
```

120 ms 感觉很紧凑——场景出现、停一拍、旁白起。150 ms 的淡入刚好够
把"砰"磨圆，不会重新引入感知差。

这个问题在那些时间线第一秒内有许多 `tl.call` 事件的场景上是隐形
的——它们与旁白同动，掩盖了间隙。所以症状在场景间表现不均（"场
景 2–5 感觉不对；场景 6 没事"），诱惑你去看场景 6 有什么不同。不
是它的问题。修复是全局的。

## 必备系统组件

- **Playwright**（`npm install playwright && npx playwright install chromium`）
  ——优先于 Puppeteer，因为它的 Chromium 自带 ARM64 构建。
  Puppeteer 即便在 aarch64 上调用，分发的也是只有 x86_64 的 `chrome`，
  目录名 `linux_arm-*` 极具误导。如果看到 "cannot execute binary
  file: Exec format error"，查 ELF 头：
  `python3 -c "open('chrome','rb').read(20)[18:20].hex()"` 返回 `3e00`
  是 x86_64、`b700` 是 aarch64。
- **ffmpeg ≥ 6**（concat 时用到 `xfade`/`acrossfade` 过滤器）。
- **fonts-noto-cjk + fonts-noto-color-emoji**，如果演示里有中文或
  emoji。没有它们字形会渲染成方块——布局不会变但可见字符会变，而
  你直到看回放某一帧才会发现。

## 双文件录制器

录制器是包在 Node 脚本外的薄 Python 壳。

- `scripts/record-html-movie.js` —— Playwright 会话：以
  `--autoplay-policy=no-user-gesture-required --mute-audio` 启动
  无头 Chromium，加载 URL，等待 `window.__movieReady`，开 CDP
  session，启动 screencast（JPEG，质量可配），每帧写一对
  `000001.jpg` + `000001.t`（时间戳，秒），轮询
  `window.__movieDone`，最后把抓到的标记导出到 `marks.json`。

- `scripts/record-html-movie.py` —— 编排器：调用 Node 脚本，读
  `marks.json`，从每帧时间戳构建一个 ffmpeg concat 列表
  （`(frame, duration)` 对），编码视频，再用 `adelay=ms|ms` +
  `amix` 在抓到的 `audio-play` 标记处锚定每场景 mp3 来构建音轨，
  最后把两者 mux 成最终 mp4。

用法：

```bash
# Full record: hits the demo at clean=1, reuses scene-named mp3s.
uv run scripts/record-html-movie.py \
    --demo path/to/demo.html \
    --out out.mp4 \
    --width 1920 --height 1080 --fps 30 --quality 84

# Title card (or any HTML with a pre-built audio track)
uv run scripts/record-html-movie.py \
    --url "file://$PWD/scripts/title.html" \
    --audio-track assets/audio/title-music.wav \
    --out title.mp4 --max-secs 15
```

输出体积：1920×1080 质量 84 时每张 JPEG 约 150–200KB → 每分钟录制
约 30–35MB。16 分钟演示的中间帧约 6 GB。最终 mp4 约 250 MB。跑完
删 `/tmp/moviecap_*`（`--keep-frames` 可保留用于调试）。

### 为什么抓帧而不用 `page.video()`

Playwright 内建的视频录制走 VP9 + WebM，帧率由编码器固定，而非
页面。GSAP 驱动的时间线下，你会在场景切换处看到帧率抖动，因为
页面瞬时空闲。CDP screencast 按页面实际绘制速度抓取（通常
30–60fps），我们在重编码时用 `-vf fps=30` 固定帧率。

## 片头 + 环境音乐

短片头（8 秒）在演示前播放，并交叉淡入第一个场景。片头是一个小
的 HTML 文件，使用同一个录制器，配一段预先做好的音轨。

- `scripts/title.html` —— 模板。CSS 动画的同心圆、漂浮的光晕、
  英雄标题、eyebrow、副标题和标语，按错峰延迟淡入。立即设
  `__movieReady=true`；在 `TITLE_DUR_SEC` 后翻 `__movieDone=true`。
  要定制，编辑那三段文字 span，可选地改 logo `<img src>`。颜色定
  义在 `:root` 自定义属性里。

- `scripts/build-title-music.sh` —— 用 ffmpeg 合成温暖的垫底音。
  叠 A2/E3/A3/C4/G4/B4 正弦波（A 小调 9 和弦声位），低通、回声、
  轻微 tremolo、淡入/淡出。纯 ffmpeg——不用音乐库。结果约 8.5 秒
  环境音，优雅垫在片头下，到交叉淡化启动时正好淡出。

要换氛围，改脚本里的频率——大调 9、小调 7、或单一持续 drone 都
可以。把 `tremolo=f=` 加大可以更闪烁；把 `aecho` 的延迟拉大可以
拖更长的混响尾。

## 交叉淡化拼接

`scripts/concat-clips.py` 把 MP4 片段拼接起来，每对相邻片段之间
加视频/音频交叉淡化。它在一个 filter graph 里使用 ffmpeg 的
`xfade` + `acrossfade` 过滤器——会全程重编码，因为交叉淡化必须
如此。

```bash
uv run scripts/concat-clips.py --out final.mp4 --fade 0.6 title.mp4 demo.mp4
```

0.4–0.8 秒的交叉淡化通常合适——太短像硬切；太长会糊掉品牌瞬间。
片头音乐的尾音（1.3 秒淡出）自然地与演示开头的旁白重叠。

## 片头场景选项：独立片段 vs. 烧进演示

两种合理模式。

**独立 title.mp4 + concat**（`scripts/title.html` 就是为此设计
的）：用 `--audio-track title-music.wav` 录片头，再录演示，用
`concat-clips.py --fade 0.7` 拼起来。当片头是通用的、或多个演示
共用时最合适。

**烧进演示作为第一个场景。** 给 `scenes` 注册表加一个 `title`
项，自带 GSAP 时间线动画 logo/标题/副标题的露出；通过
`<audio id="audio-title" src="./assets/audio/title-music.wav">`
加载片头音乐；把 `title: 'why-field'`（或你的下一个场景名）放在
`SCENE_CHAIN` 顶部。录制器会自动识别——它只是个普通场景。没有
concat 步骤、没有交叉淡化伪影，浏览器内预览也带片头——与视频体
验一致。

当演示会被频繁重渲染、且片头属于*这个*演示品牌的一部分时，选
"烧进去"。当你可能给不同受众换片头、或同一份演示要配多套开场
时，选"独立"。

## 浏览器内观看模式（"像视频一样播"的 UX）

驱动录制器的同一份 HTML 也可以成为可分享的观看体验——不需要录
制步骤。三处调整把可拖动的演示页变成有视频感的播放器：

1. **沉浸式布局** —— 隐藏右侧栏；让舞台占满内容宽度。用
   `body[data-immersive="true"]` 和*排除 `.grain`* 的选择器
   （见下一条坑点）：

   ```css
   body[data-immersive="true"] > main > div:not(.grain) > aside { display: none !important; }
   body[data-immersive="true"] > main > div:not(.grain) {
     grid-template-columns: 1fr !important;
     max-width: 1280px !important;
   }
   ```

2. **故事文字 → 进度条提示框。** 把节拍列表从右侧栏移到进度条
   标记上的可 hover 提示框里。在 `renderBeats` 中给每个标记挂
   一个 `.tooltip` 子节点，内容为该节拍的 `clk` / `label` /
   `hud`。再在进度条上方显示一个小的 "now-strip" 展示当前节拍的
   label。

3. **外框切换。** 右上角的浮动按钮（和 `F` 键）翻转
   `body[data-chrome="off"]`。CSS 通过 `transform:
   translateY(±100%)` 和 `transition: transform 320ms` 把头部上
   滑、底部下滑。在已提交关闭状态下，鼠标靠近顶或底边时，边缘
   揭示处理器把它们瞬时显出来，鼠标离开 1.2 秒后再隐藏：

   ```js
   let chromeCommitted = 'on', chromeRevealed = false, revealTimer = null;
   function setChrome(t) { chromeCommitted = t; chromeRevealed = false;
                            clearTimeout(revealTimer); document.body.dataset.chrome = t; }
   document.addEventListener('mousemove', e => {
     if (chromeCommitted !== 'off') return;
     const inEdge = e.clientY < 60 || e.clientY > innerHeight - 80;
     if (inEdge) { clearTimeout(revealTimer);
                   document.body.dataset.chrome = 'on'; chromeRevealed = true; }
     else if (chromeRevealed) {
       clearTimeout(revealTimer);
       revealTimer = setTimeout(() => {
         if (chromeRevealed && chromeCommitted === 'off') {
           document.body.dataset.chrome = 'off'; chromeRevealed = false;
         }
       }, 1200);
     }
   });
   ```

   两态模型（"已提交" vs "瞬时显出"）是微妙之处——没有它，外
   框栏会闪烁或拒绝重新隐藏。

## 常见坑点

**宽泛的子选择器会命中装饰兄弟元素。** 当你写
`body[data-immersive="true"] > main > div { max-width: 1280px;
... }`，它会命中 `<main>` 的*每个*直接子 div——包括作为内容容器
兄弟节点的、绝对定位的 `<div class="grain">` 噪点叠层。grain 会
被收缩到内容的 max-width，只覆盖舞台的一部分，看上去像半幅叠
层。始终显式排除装饰兄弟：`> main > div:not(.grain)`。一般教
训：当页面有绝对定位的叠层兄弟时，写选择器要按 class 定位内容
div（`> .content-wrap`）或用 `:not(...)` ——绝不要单靠标签/位置。

**HiDPI 下 grain 噪点看起来"低分辨率"。** 一种常见做法是用 SVG
fractal-noise data URI 作为平铺背景。如果 SVG 只有 `viewBox` 而
没有显式 `width`/`height`，浏览器会按 viewBox 的固有大小（通常
200px）光栅化后再平铺。Retina 显示器上你看到的就是重复的 200
像素图样，而非细密颗粒。

修法：显式设 `width="256" height="256"`，把 `baseFrequency` 提
高到约 `2.6`（噪点更细），加 `stitchTiles="stitch"` 让平铺接缝
无缝，再用 `feColorMatrix` 把彩色 turbulence 转成白色带 alpha
（更像真正的胶片颗粒）：

```css
background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='256' height='256'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='2.6' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.65 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
background-size: 256px 256px;
opacity: 0.05;
```

把 `opacity` 降到 0.04–0.06——同样的视觉存在感，在低码率编码下
伪影更少。

**音频在浏览器里能响但抓出来是哑的。** 符合预期——我们用
`--mute-audio` 并在 Python 中单独重建音轨。如果最终 mp4 无声，
检查 `marks.json` 是否有 `audio-play` 条目（只有 clean 模式钩子
接好了才会出现）。

**第一帧无样式，或外框短暂闪现。** 把 clean 模式 CSS 放到演示
其他 CSS 同一个 `<style>` 块（不要放到首次绘制后才加载的独立
样式表），并确保 JS 在启动 `loadScene()` 之前同步设置
`document.body.dataset.clean = 'true'`。

**`xfade` 报错 "Inputs do not match"** 拼接时。意味着两个片段
的 pix_fmt、分辨率或帧率不同。在 concat 前用相同参数
（`-pix_fmt yuv420p -r 30`）重新编码各片段，或始终走
`record-html-movie.py`，它产出的参数本身就一致。

**场景画面早于音频。** 默认 `loadScene` 在音频淡入前加 500ms 延
迟。我们的 audio-play 标记精确捕获这个延迟（视觉标记先 fire，
500ms 后音频标记再 fire），而 `adelay` 用的是 audio-play 标记——
所以它们对齐。如果你看到音频领先画面，说明你的标记接到了
scene-active 事件而不是 audio-play 事件。

**ARM64 Chromium 失败。** Puppeteer 的 `@puppeteer/browsers
install` 即便在 aarch64 上也硬编码 x86_64 二进制。改用 Playwright
（`npx playwright install chromium`）——它有标注为 "fallback
build for ubuntu24.04-arm64" 的独立 ARM64 构建。录制器之所以用
Playwright，正是为此。

**无头 chromium 对超高内容无法合成 screencast。** 如果某个场景
内容超过 1080px 高，你会看到顶部被抓取、其余被裁掉。clean 模式
CSS 把场景在视口内垂直居中，所以一般没事——但运行完整录制前，
先用 `tools/screenshot-scenes.js` 复核溢出。
