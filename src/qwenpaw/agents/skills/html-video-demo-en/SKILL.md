---
name: html-video-demo
description: Build single-file HTML "video demos" — scripted timelines of UI choreography that play end-to-end like a guided product walkthrough or story-mode landing page. Captures the patterns that hold up across very different scenes (mobile lock screen, plugin overlay, productivity app, creative tool, dashboard, terminal) — scene registry, axis HUD, workspace-asset activation, pipeline stage cards, state machines inside cards, text-typing helper, auto-scroll, cursor for tap simulation, mood theming, SVG illustrations, Web Audio SFX, reset patterns. Use this skill when the user asks for an interactive HTML walkthrough, an embedded demo for a landing page, or a story-mode "watch what it does" page that plays in the browser without backend or build step. Optional voice narration with auto-aligned visuals via the audio-narration reference. Optional MP4 export with title card + bg music via the video-export reference.
metadata:
  builtin_skill_version: "1.0"
---

# Single-file HTML demos with scripted UI choreography

A "video demo" is one HTML file that plays like a guided product tour: scripted UI animations on a GSAP timeline, persona switcher, transport controls, and a story map. The viewer hits play and watches; they can pause, scrub, switch personas, or just let it run. This skill captures the patterns that held up across six very different scenes (lock-screen, plugin overlay, productivity app, creative tool, light dashboard, terminal) — the architecture, the recurring component patterns, and the gotchas you only learn by shipping.

## When to use this skill

- You want a **product walkthrough or "story mode"** that plays in a single self-contained HTML file
- The page has **time-based UI choreography** (GSAP, Anime.js, CSS animations, or hand-rolled JS)
- You're **not building a video** — you want a real interactive HTML page where the viewer can scrub, pause, switch between scenes, and inspect element
- The user wants to share a single URL or file, not a video upload
- Optionally: layer **TTS voice narration** with auto-aligned visuals — see `references/audio-narration.md`. (Skippable; the HTML patterns stand on their own.)

## Stack

Pick the minimum that works:

- **GSAP** (CDN) — timeline + tweens + callbacks
- **Tailwind** (CDN play script) — utility classes for chrome and layout. Bring your own CSS for anything component-shaped.
- **Google Fonts** — Inter + JetBrains Mono is a strong default pair
- **Inline SVG** for any illustrations / iconography
- **Web Audio API** for one-off SFX (phone buzz, alert ping) — don't pull a sound library

No build step. The whole demo is one `.html` file plus an `assets/` folder.

## Top-level architecture

One `scenes` registry. Each scene is a plain JS object:

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

A single `loadScene(id)` function orchestrates:

1. Kill the previous timeline (`prevTl.pause(); prevTl.kill()`)
2. Toggle `data-active="true"` on the new scene's `<section>`, `false` on others
3. Re-render the beat list + scrubber markers for the new scene
4. Call `scene.reset()` to wipe visual state
5. Build the new timeline (paused)
6. Start playback after a short delay

## The five shared elements every demo needs

| Element | Lives where | Purpose |
|---|---|---|
| **Scene section** | `<section id="scene-{id}" class="scene">` inside the stage | Container for all scene-specific HTML |
| **Right rail** | Shared across scenes | Now caption · axis HUD · story map (beat list) |
| **Transport** | Bottom bar | Play / restart / scrubber / mute / scene label |
| **Persona strip** | Top bar | Quick scene switcher |
| **Closing strip** | Below the stage | Closing SVG + caption that slides in at scene end |

The right rail and transport are **shared** — they re-render content for whichever scene is active. The scene sections are **swappable** via `data-active`.

```css
.scene { display: none; }
.scene[data-active="true"] { display: flex; flex-direction: column; align-items: center; }
```

## The beat system

`beats: [{ t, clk, label, hud }, ...]` is the spine of the story.

- `t` (seconds, scene-time) — when this beat becomes "active"
- `clk` — fake wall-clock string shown to the viewer (e.g., `'03:14:02'`)
- `label` — short title for the story map and current-beat caption
- `hud` — longer sentence shown in the axis-detail line; this is where you spell out *which axis / system component is doing what*

A single `syncMeta(t)` function called via the timeline's `onUpdate` figures out the active beat:

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

State on each beat row is driven entirely by `data-state` attributes — CSS does the rest. No per-element JS state.

## The axis HUD pattern

A persistent row of N "axis pills" at the top of the right rail (5 is a good number, but use as many as your architecture defines). Each pill has three visual states:

- **Idle**: muted color
- **Active**: pulses, accent color, scaled slightly
- **Fired**: persistent dim color showing it was used during this scene

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

A `pulseAxis(name, holdSec)` helper called from the timeline:

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

This single visual element does heavy lifting — it's how a viewer learns the architecture vocabulary while watching the demo. Pair it with `hud` strings in the beats that name the same axis ("Skills · pulling X") and the vocabulary lands twice per beat.

## Surface variety: one window pattern per persona

Don't reuse the same window chrome for every scene. The surface should look like the world that persona actually works in:

| Persona archetype | Surface | Aesthetic notes |
|---|---|---|
| On-call ops | Phone lock screen | Dark wallpaper, dynamic island, stacked notification cards |
| Enterprise IM user | Chat-app plugin (overlay) | Light theme, side panel, host-app brand visible |
| Knowledge worker (CN) | Productivity wiki (Yuque-style) | Soft borders, generous padding, sidebar with folders |
| Creative pro | Pro tool (DaVinci-flavor) | Dark, monospace filenames, color-coded scores |
| Data analyst | Light inbox / dashboard | Outlook-ish palette, charts as artifacts |
| Hedge-fund / trader | Bloomberg-style terminal | Pitch black, amber monospace, dense info |

For each surface, decide:
- **Window dimensions** (920×580 is a good default)
- **Color palette** (3–4 colors max plus a single accent)
- **Typography** — body sans + monospace; add CJK fallback (`PingFang SC`) where Chinese is shown
- **macOS-style traffic lights** (`<span class="r"><span class="y"><span class="g">`) sell "this is an app window" cheaply
- **Window-internal toolbar** with brand mark + path / title

## Workspace-asset activation pattern

When the demo's "agent" reads N source materials, show them as a list in the sidebar and **light them up as each is read**:

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

Driven from the timeline:

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

This single pattern makes "the agent uses *these specific files*" visible — without it, generation looks like magic.

## Pipeline stage cards

For multi-stage processes (SQL → chart → narrative; pdf-parse → diff → synthesize → translate), use stacked cards that pulse through `waiting → active → done`:

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

Each stage card can host its own visualizations — SQL syntax-highlighted, mini bar charts, a horizontal "scan" bar for z-score gates. Decorate freely; keep the surrounding state machine consistent.

## State machine within a single card

Sometimes a single UI element transitions through multiple stages — e.g., a notification card that goes diagnosing → hypothesis-with-buttons → executing → resolved, or a generation card that goes queued → generating (shimmer) → still (image) → animating → animated (image with Ken Burns + play badge).

Pattern: one outer element with `data-stage` attribute, multiple inner blocks show / hide based on stage:

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

Reversibility note: `data-attribute` changes via `.call()` only fire forward. If scrubbing backward needs to "undo" a stage, use `gsap.set` and reverse-set pairs, or just accept that forward scrubbing is the supported direction.

## Text-typing helper

For long text appearing progressively — a single helper:

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

`gsap.set(..., { textContent: '...' })` works fine — GSAP assigns properties directly. Each step costs one tween slot but they're cheap.

For CJK text use a smaller `charsPerStep` (2–3); for Latin alphabet 4–5 reads naturally.

## Auto-scroll for growing panels

When a panel accumulates content (typed-in document, scrolling log, growing pipeline list), scroll to keep the latest content visible:

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

CSS: `overflow-y: auto; scroll-behavior: smooth;` on the panel.

Alternative for chat-style messages where newest stays at bottom: `display: flex; flex-direction: column; justify-content: flex-end; overflow: hidden;` — content packs to bottom and overflows off the top automatically.

## Cursor for tap simulation

A small floating element that animates to a target position to simulate clicking:

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

In the timeline:

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

The `transform: translate(-50%, -50%)` makes `left:74%; top:87%;` mean "cursor *center* at that position." GSAP can still scale the cursor because scale composes with the centering transform.

Position relative to a known container (usually the window or stage). Percentage coords work; pixel-perfect alignment isn't necessary.

## Scene mood / theming

Per-scene atmospheric tweaks via a single attribute:

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

`loadScene()` sets the mood:
```js
document.getElementById('stage-bg').dataset.mood = scenes[id].stageMood;
```

Subtle but effective for differentiating a 3 a.m. scene from a Monday-morning one without redoing the whole window aesthetic.

## SVG illustrations as scene previews

When the demo references "videos" or "images" that don't exist yet, inline data-URI SVGs sell the illusion cheaply:

```css
.scene-img.coffee-shot {
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 50' preserveAspectRatio='xMidYMid slice'><rect width='80' height='50' fill='%23451a03'/><ellipse cx='40' cy='32' rx='22' ry='5' fill='%231c1917'/><!-- … --></svg>");
  background-size: cover;
  background-position: center;
}
```

Rules for inline SVG-in-CSS:
- Use `'` (single quotes) for HTML attrs inside the data URI; `"` outside
- URL-encode `#` as `%23` (color values, `url(#gradId)` references)
- Use `<defs>` + gradients to add depth cheaply
- 80×50 viewBox slices well across vertical / square / landscape aspect ratios
- 4–6 colored shapes is enough to suggest a scene; don't try to draw photos

The same illustration can serve a clip thumbnail (40×24), a sidebar icon (44×26), a render preview (24×40), and a hero shot (320×180) — `preserveAspectRatio="xMidYMid slice"` handles all of them.

## Web Audio for one-off SFX

Don't ship a sound library. For a brief sound effect (phone buzz, alert ping, button click), synthesize it:

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

Prime the AudioContext on any user gesture (otherwise `playBuzz` is silent due to autoplay policy):

```js
['click', 'keydown', 'touchstart'].forEach(ev =>
  window.addEventListener(ev, () => {
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  }, { passive: true })
);
```

## Reset patterns

Every scene needs a `reset()` that returns it to the t=0 state. It runs before the timeline plays from the start (initial load and restart).

Things that need explicit resetting (anything the timeline *changes*):
- Element opacity, transform, custom CSS properties
- `data-state`, `data-stage`, `data-active` attributes
- `textContent` of any element the timeline writes to
- Dynamically created children (clear `innerHTML`)
- Cursor positions
- Closing strip opacity + transform

```js
reset() {
  gsap.set(['#card-1', '#card-2', '#card-3'], { opacity: 0, y: -12 });
  document.querySelectorAll('.ws-asset').forEach(el => el.dataset.state = 'waiting');
  document.getElementById('output-list').innerHTML = '';
  gsap.set('#closing-strip', { opacity: 0, y: 20 });
  // ...
}
```

A scene's `reset()` typically grows to 20–40 lines. That's fine. The alternative — making the timeline naturally restore everything by reversing — is more fragile.

## Common gotchas

**GSAP `tl.set({}, { textContent: '...' })`** does work, but only on real DOM elements, not jQuery-like collections. Always pass a single selector string or a single Element.

**`overflow: hidden` + `position: absolute` children** is fine — but `position: relative` on the container is needed if you want the absolute children to position relative to it. Common bug: cursor anchored to `body` because the container forgot `position: relative`.

**Tailwind CDN's MutationObserver** picks up dynamically-inserted DOM, so `innerHTML = '<div class="bg-red-500">...'` works. But the first paint of the dynamic content may flash unstyled briefly. For demo timing this is usually invisible; if it bothers you, write the class to plain CSS.

**Multiple `tl.set()` on the same property at the same time** — the last one wins. Useful for "this element starts hidden and at offset y=-12" without writing `gsap.set` for initial state separately.

**`gsap.timeline({ paused: true })` is required** if you're driving the timeline from an external clock (e.g., audio narration). Otherwise the timeline auto-plays and fights your seek calls.

**Closing-strip animation interference** — the closing strip is shared across scenes (one DOM element with `opacity: 0` reset by each scene). When switching scenes mid-play, kill the previous timeline first to prevent stale tweens animating it.

**`gsap.to(el, { className: '+=foo' })`** supports class manipulation but is brittle across GSAP versions. Prefer plain `el.classList.add(...)` inside a `.call()`, or — better — use `data-state` attributes driven by CSS selectors.

**Persona-strip "active" highlight** should be reset on every `loadScene()`. Don't rely on the old active state for anything beyond the visual.

## Single-file packaging

The demo should open by double-click — no server needed.

- All CSS inline in `<style>`
- All JS inline in `<script>`
- Audio + SVG illustrations as relative `./assets/...` references (browser `file://` works)
- One CDN script tag each for GSAP and Tailwind; one `<link>` for Google Fonts

If you need *truly* offline-portable single file:
- Inline the GSAP source (~70 KB)
- Inline Tailwind's static build (`tailwindcss` CLI build, ~10 KB after purge)
- Embed audio as data URIs (only if total < 5 MB; otherwise keep them external)
- Embed scene SVGs the same way (already done above)

For normal demos, the CDN-and-relative-assets approach is fine and keeps the file readable.

## Adding voice narration (optional)

Add a TTS voice-over that **stays aligned to the visuals** even as you edit the script — the audio becomes the master clock and the GSAP timeline auto-seeks to follow. The pattern uses either OpenAI's TTS or Alibaba DashScope's Qwen-TTS for synthesis (the script picks based on which API key is in the env; if both are present it asks), Whisper for timestamps, and a small set of `[audioTime, sceneTime]` "checkpoint" anchors per scene.

The pieces live in `scripts/` (TTS generation, Whisper transcription, timestamp dump) and the full workflow + HTML wiring is documented in **`references/audio-narration.md`**. Read that before adding audio to a scene.

Quick mental model:
- Write narration as plain `.txt` files (one per scene)
- `generate-tts.py` → mp3 per scene
- `transcribe.py` → word-level timestamps per scene
- `dump-timestamps.py` → phrase-level pretty-print for picking anchor moments
- Add `checkpoints: [[audioT, sceneT], ...]` to each scene config
- A `requestAnimationFrame` loop reads `audio.currentTime`, interpolates between checkpoints, and calls `timeline.time(sceneT)` — non-uniform pacing falls out for free

## Exporting to MP4 (optional)

When the user asks for a shareable video, the demo can be exported to a single MP4 with a title card + ambient music — without rewriting it into a video-framework composition format (HyperFrames, Remotion, etc.). The pipeline is Playwright + CDP screencast for video, Python + ffmpeg `adelay`/`amix` for audio, all driven by the same per-scene mp3s already on disk.

Key idea: the GSAP timeline is driven by `audio.currentTime`, so capturing the headless browser's screen output and concatenating the same audio files at the captured `audio-play` moments yields frame-perfect sync without trying to record desktop audio.

The pattern requires the demo to implement a small `?clean=1` mode (hide chrome, force-chain all scenes, emit marks to `window.__movieMarks`, set `__movieDone` at the end). Full workflow, the clean-mode CSS+JS skeleton, the title template, quality knobs (`--dpr 2` is the biggest single quality lever), the audio-sync correction, and gotchas (broad-child-selector siblings, grain SVG resolution, ARM64 Chromium, CJK font availability, encoder pix_fmt mismatches) are documented in **`references/video-export.md`**.

Quick mental model:
- Implement the clean-mode contract in the demo (drop-in CSS + JS block — see reference)
- `record-html-movie.py --demo demo.html --out demo.mp4 --dpr 2 --crf 16 --preset slow` → captures at 2× then Lanczos-downsamples to 1080p for retina-quality output
- Customize `scripts/title.html` (text + colors), then `record-html-movie.py --url title.html --audio-track title-music.wav --out title.mp4` — OR bake the title scene into the demo's scene registry and skip the concat step entirely
- `build-title-music.sh` synthesizes ambient pad via ffmpeg sine stack
- `concat-clips.py title.mp4 demo.mp4 --out final.mp4 --crf 16 --preset slow` joins with a crossfade (only needed if title is a separate clip)

## In-browser viewing mode (optional, complements video export)

The same HTML can also be a polished "watch end-to-end like a video" page in any modern browser — no recording step. Three additive tweaks make this work:

- `body[data-immersive="true"]` hides the right rail and expands the stage to a centered single column
- Story-map beat text moves from the right rail into **hover tooltips on the scrubber markers**, plus a tiny "now-playing" caption above the scrubber
- A floating button (and the **F** key) collapses the topbar + footer; an edge-reveal handler temporarily slides them back when the mouse approaches the top/bottom edge

This delivers the same UX as the rendered MP4 but inside the page — scrubbable, with full DOM inspection still available. The patterns and the two-state ("committed" + "transient-revealed") chrome-toggle logic are documented in `references/video-export.md`.

## Files in this skill

- `scripts/generate-tts.py` — call OpenAI Speech API or DashScope Qwen-TTS on per-scene `.txt` files, write `.mp3` (backend auto-selected by available API key; both honored via `OPENAI_API_KEY` / `DASHSCOPE_API_KEY`)
- `scripts/transcribe.py` — call Whisper on each `.mp3`, write word-level `.json`
- `scripts/dump-timestamps.py` — pretty-print phrase-level transcripts for picking anchor times
- `scripts/record-html-movie.py` + `.js` — record the demo to MP4 (Playwright + CDP screencast + ffmpeg mux)
- `scripts/title.html` — title-card template; edit eyebrow/title/subtitle/tagline + logo
- `scripts/build-title-music.sh` — ffmpeg synth of a warm A-minor-9 ambient pad
- `scripts/concat-clips.py` — join MP4 clips with `xfade`/`acrossfade`
- `references/audio-narration.md` — full workflow, HTML wiring snippets, voice tuning, audio-specific gotchas. Read **only** if you're adding narration.
- `references/video-export.md` — full workflow for MP4 export: clean-mode contract, recorder details, title + music, gotchas. Read **only** if you're rendering a video.
