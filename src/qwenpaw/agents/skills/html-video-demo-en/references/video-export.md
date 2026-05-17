# Exporting an HTML movie demo to MP4

Sometimes the demo needs to leave the browser — a video the user can drop in
Slack, email, or a deck. This reference covers the end-to-end pipeline:
clean mode in the HTML → frame capture → audio assembly → title + music →
final concat. The tools mentioned live in `scripts/` of this skill and are
copy-into-project ready.

## What the pipeline actually does

The demo's GSAP timeline is driven by `audio.currentTime` (audio is the
master clock — see `audio-narration.md`). That means whatever the browser
*renders* is exactly aligned to whatever audio file is playing at the
moment. Recording is therefore two independent streams:

1. **Video** — a Playwright/Chromium session with `--mute-audio` plays the
   demo end-to-end while CDP screencast streams JPEG frames to disk.
2. **Audio** — the same per-scene `.mp3` files the browser played are
   concatenated in Python with `adelay` so each starts at the exact moment
   the browser actually started playing it.

We mux them at the end. Because both streams reference the same audio
clock, frame-perfect sync falls out for free.

We do **not** use HyperFrames or any HTML-to-video framework that requires
its own composition format (e.g. `data-start`/`data-duration` attributes on
every animated element). The existing demo's audio-master-clock pattern is
incompatible with those formats. The pipeline below builds on the same
primitives those frameworks use under the hood — Puppeteer/Playwright +
CDP screencast + ffmpeg — and honors the demo's existing timeline.

## The clean-mode contract the demo must implement

The recorder loads the demo with `?clean=1`. The demo's job:

1. **Hide chrome** via a CSS branch keyed on `body[data-clean="true"]` —
   topbar, right rail, transport, modals. Expand the stage to fill the
   viewport. *Don't* delete chrome elements; many scenes update DOM nodes
   inside the right rail (`caption-text`, `axis-detail`, beat rows) and
   removing them throws null-deref errors.

2. **Force-chain all scenes** that wouldn't normally auto-advance. Most
   demos pause at a "viewer picks the next persona" gate; in clean mode
   you patch the chain so it runs straight through to the last scene.

3. **Emit marks for the recorder.** A `MutationObserver` on every
   `section.scene` watches `data-active` flips; an `addEventListener('play'`
   on each `<audio id="audio-*">` captures the precise moment narration
   starts. These land in `window.__movieMarks = []`.

4. **Signal start and end.** Set `window.__movieReady = true` after the
   first scene is wired (the recorder waits for this before starting the
   screencast). Set `window.__movieDone = true` after the final scene's
   audio fires `ended` (the recorder polls for this to know when to stop).

The full skeleton (drop this near the end of your demo's main script,
right before the boot `loadScene(...)` call):

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

The companion CSS (paste near the bottom of your demo's `<style>`):

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

The exact selectors depend on your demo's layout, but the principle is
universal: hide the chrome, expand the stage area to a centred 1180px
column inside a 1920×1080 viewport, and keep the grain noise overlay off
(at low encoder bitrates it strobes).

Why 1180px? It's the design width of the typical "scene" content in this
skill (lock-screen, plugin overlay, productivity app, etc.). The
centred column on a 1920×1080 canvas gives ~370px of letterbox on each
side — perfectly composed for video without resizing scene internals.

## Quality knobs — pick the right ones up front

Three settings have outsized effect on how the final video looks. Pick
them deliberately before kicking off the long capture.

**`--dpr 2` (capture at 2× pixel density).** The biggest single quality
lever. Playwright renders the page at viewport×DPR physical pixels and
the CDP screencast captures that. Encoding then downscales with
`scale=W:H:flags=lanczos`. The downsampling acts as antialiasing — text
and thin lines look the way a retina display renders them. Without
`--dpr 2`, a 1080p output looks soft because the live demo on the
viewer's retina display *is* effectively 2× supersampled. Match it.

**`--quality 88` JPEG screencast, `--crf 16 --preset slow` x264.** The
screencast quality is the *source* fidelity — CRF can never recover
what JPEG already lost. q=88 is a good compromise; q=92 is visually
transparent and ~15% larger. For the x264 encoder, `preset slow + crf
16` is the sweet spot for screencast content: detail-preserving but not
overkill like `crf 14` which adds 30% size for no perceptual gain.

**Disk budget.** At `--dpr 2` and JPEG q=88, frames average ~110 KB at
1080p logical (3840×2160 captured). A 15-minute demo produces ~5 GB of
intermediate frames. Plan for 7–8 GB scratch space; clean up
`/tmp/moviecap_*` after each run.

Avoid the trap of going to 4× DPR or `crf 12`. They double the
intermediate size and roughly halve the encode speed for differences
that don't survive YouTube/Slack re-encoding.

## Audio sync — the pre-audio delay matters

In live (interactive) playback, `loadScene()` waits 500 ms before
calling `audio.play()`, then audio fades in over 500 ms. The fade-in
masks the visual-versus-narration gap — the viewer hears the volume
rise as the scene appears.

In the recorded video, the fade-in is *missing* (our audio mux uses
`adelay` to drop the mp3 in at the captured `audio-play` mark, then it
plays at full volume immediately). With the live 500 ms delay still in
place, the audio "pops in" abruptly ~1 second after the visual scene
appears — and on scenes with static visuals (a title fade-in + a list
of bullets, no dynamic animation between scene-active and end), the
viewer perceives this as "audio lagging behind the scene."

The fix is to tighten the pre-audio delay and fade-in **only when
`?clean=1` is set** — keep live behavior unchanged:

```js
const preAudioDelayMs = CLEAN_MODE ? 120 : 500;
const fadeInDur       = CLEAN_MODE ? 0.15 : 0.5;
setTimeout(() => {
  audioFadeIn(currentAudio, fadeInDur).then(...);
}, preAudioDelayMs);
```

120 ms feels snug — the scene appears, beat, then narration. The 150 ms
fade-in is just enough to round off the "pop" without re-introducing
the perception gap.

This problem is invisible on scenes whose timelines have many `tl.call`
events firing within the first second — they animate alongside the
narration, masking the gap. So the symptom shows up unevenly across
scenes ("scenes 2–5 feel off; scene 6 is fine") and the temptation is
to look at scene 6 for what's different. It's not. The fix is global.

## Required system bits

- **Playwright** (`npm install playwright && npx playwright install chromium`)
  — preferred over Puppeteer because its Chromium ships ARM64 builds.
  Puppeteer ships an x86_64-only `chrome` even when invoked on aarch64,
  and the `linux_arm-*` directory name is misleading. If you see "cannot
  execute binary file: Exec format error", check the ELF header:
  `python3 -c "open('chrome','rb').read(20)[18:20].hex()"` returns `3e00`
  for x86_64 and `b700` for aarch64.
- **ffmpeg ≥ 6** (uses the `xfade`/`acrossfade` filters in concat).
- **fonts-noto-cjk + fonts-noto-color-emoji** if your demo has Chinese
  text or emoji. Without them, glyphs render as boxes — the layout
  doesn't change but the visible characters do, and you won't notice
  until you watch a frame.

## The two-file recorder

The recorder is a thin Python wrapper around a Node script.

- `scripts/record-html-movie.js` — Playwright session: launches headless
  Chromium with `--autoplay-policy=no-user-gesture-required --mute-audio`,
  loads the URL, waits for `window.__movieReady`, opens a CDP session,
  starts a screencast (JPEG, configurable quality), writes one
  `000001.jpg` + `000001.t` (timestamp in seconds) pair per frame, polls
  `window.__movieDone`, dumps `marks.json` with the captured marks.

- `scripts/record-html-movie.py` — orchestrator: invokes the Node script,
  reads `marks.json`, builds an ffmpeg concat list of `(frame, duration)`
  pairs from the per-frame timestamps, encodes video, builds the audio
  track from per-scene mp3s anchored at the captured `audio-play` marks
  using `adelay=ms|ms` + `amix`, muxes the two into the final mp4.

Usage:

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

Output sizes: ~150–200KB per JPEG at 1920×1080 quality 84 → ~30–35MB per
captured minute. A 16-minute demo lands around 6 GB of intermediate
frames. The final mp4 is ~250 MB. Delete `/tmp/moviecap_*` after the run
(`--keep-frames` keeps it for debugging).

### Why we capture frames instead of using `page.video()`

Playwright's built-in video recording goes through VP9 + WebM with a
fixed framerate decided by the codec, not by the page. With a
GSAP-driven timeline you'll see frame-rate hitching at scene
transitions where the page momentarily idles. CDP screencast captures
at whatever rate the page actually paints (typically 30–60fps), and we
fix the rate at re-encode time via `-vf fps=30`.

## Title card + ambient music

A short title card (8 seconds) plays before the demo and crossfades into
the first scene. The title is a small HTML file that uses the same
recorder, with a pre-built audio track.

- `scripts/title.html` — the template. CSS-animated rings, drifting
  glows, a hero title, eyebrow, subtitle, and tagline that all fade in
  at staggered delays. Set `__movieReady=true` immediately; flip
  `__movieDone=true` after `TITLE_DUR_SEC`. To customize, edit the
  three text spans and (optionally) the logo `<img src>`. The colours
  live in `:root` custom properties.

- `scripts/build-title-music.sh` — synthesizes a warm pad with ffmpeg.
  Stacks A2/E3/A3/C4/G4/B4 sine waves (A minor 9 voicing), low-passes,
  echoes, slight tremolo, fade in/out. Pure ffmpeg — no music libs. The
  result is ~8.5s of ambient that sits gracefully under the title and
  fades out by the time the crossfade kicks in.

For a different mood, change the frequencies in the script — major-9
voicings, minor-7s, or a single sustained drone all work. Increase the
`tremolo=f=` value for more shimmer; raise the `aecho` delays for more
reverb tail.

## Concatenating with a crossfade

`scripts/concat-clips.py` joins MP4 clips with a video/audio crossfade
between every adjacent pair. It uses ffmpeg's `xfade` + `acrossfade`
filters in one filter graph — fully re-encoded because crossfades
require it.

```bash
uv run scripts/concat-clips.py --out final.mp4 --fade 0.6 title.mp4 demo.mp4
```

A 0.4–0.8s crossfade is usually right — too short feels like a hard cut;
too long blurs the brand moment. The title music's tail (1.3s fade-out)
overlaps naturally with the demo's opening narration.

## Title scene options: separate clip vs. baked into the demo

Two valid patterns.

**Separate title.mp4 + concat** (what `scripts/title.html` is designed
for): record the title with `--audio-track title-music.wav`, record the
demo, join with `concat-clips.py --fade 0.7`. Best when the title is
generic or shared across multiple demos.

**Baked into the demo as the first scene.** Add a `title` entry to the
`scenes` registry with its own GSAP timeline animating the
logo/headline/subtitle reveals; load the title music via
`<audio id="audio-title" src="./assets/audio/title-music.wav">`; put
`title: 'why-field'` (or whatever's first) at the top of
`SCENE_CHAIN`. The recorder picks it up automatically because it's
just another scene. No concat step, no crossfade artifact, and the
in-browser preview opens with the title too — same experience as the
video.

Pick "baked in" when the demo will be re-rendered often and the title
is part of the brand for *this* demo. Pick "separate" when you might
swap titles per-audience or share the same demo with multiple intros.

## In-browser viewing mode (the "play it like a video" UX)

The same HTML that drives the recorder can also be the shareable
viewing experience — no recording step needed. Three tweaks turn the
scrubbable demo page into a video-feeling player:

1. **Immersive layout** — hide the right rail; let the stage take the
   full content width. Use `body[data-immersive="true"]` and selectors
   that *exclude `.grain`* (see the next gotcha):

   ```css
   body[data-immersive="true"] > main > div:not(.grain) > aside { display: none !important; }
   body[data-immersive="true"] > main > div:not(.grain) {
     grid-template-columns: 1fr !important;
     max-width: 1280px !important;
   }
   ```

2. **Story text → scrubber tooltips.** Move the beat list out of the
   right rail and into hoverable tooltips on the scrubber markers. In
   `renderBeats`, attach a `.tooltip` child to each marker with the
   beat's `clk` / `label` / `hud`. Also show the current beat's label
   in a small "now-strip" above the scrubber.

3. **Chrome toggle.** A floating top-right button (and the `F` key)
   flips `body[data-chrome="off"]`. CSS slides the header up and the
   footer down via `transform: translateY(±100%)` and `transition:
   transform 320ms`. While committed-off, an edge-reveal handler
   transiently shows them when the mouse approaches the top or bottom
   edge, then hides them again 1.2 s after the mouse leaves:

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

   The two-state model ("committed" vs "transiently revealed") is the
   subtle bit — without it the bar flickers or refuses to go back away.

## Common gotchas

**Broad child selectors capture decorative siblings.** When you write
`body[data-immersive="true"] > main > div { max-width: 1280px; ... }`,
it matches *every* direct-child div of `<main>` — including the
absolutely-positioned `<div class="grain">` noise overlay that sits as
a sibling of the content wrapper. The grain ends up shrunken to the
content max-width and only covers a portion of the stage, looking like
a partial overlay. Always exclude decorative siblings explicitly:
`> main > div:not(.grain)`. The general lesson: when the page has
absolutely-positioned overlay siblings, write selectors that target the
content div by class (`> .content-wrap`) or `:not(...)` — never by
tag/position alone.

**Grain noise looks "low-res" at HiDPI.** A common pattern is an SVG
fractal-noise data URI as a tiling background. If the SVG has only a
`viewBox` and no explicit `width`/`height`, browsers rasterize it at
the viewBox's intrinsic size (often 200 px), then tile. On a retina
display you see a repeating 200-pixel pattern instead of fine grain.

Fix: set explicit `width="256" height="256"`, raise `baseFrequency` to
~`2.6` (much finer noise), add `stitchTiles="stitch"` for seamless tile
boundaries, and pipe through `feColorMatrix` to convert the colored
turbulence into white-with-alpha (proper film-grain look):

```css
background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='256' height='256'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='2.6' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.65 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
background-size: 256px 256px;
opacity: 0.05;
```

Drop `opacity` to 0.04–0.06 once the noise gets finer-grained — same
visual presence, fewer artifacts during low-bitrate encoding.

**Audio plays in the browser but capture is silent.** Expected — we
`--mute-audio` and rebuild the audio track separately in Python. If the
final mp4 has no sound, check that `marks.json` has `audio-play` entries
(they only fire if the demo's clean-mode hook is wired correctly).

**The first frame is unstyled or shows the chrome briefly.** Move the
clean-mode CSS into the same `<style>` block as the rest of the demo
(not a separate stylesheet that loads after first paint), and ensure the
JS sets `document.body.dataset.clean = 'true'` synchronously before the
boot `loadScene()` call.

**`xfade` errors with "Inputs do not match"** when concatenating. Means
the two clips have different pix_fmt, resolution, or framerate. Re-encode
each clip with the same settings (`-pix_fmt yuv420p -r 30`) before
concat, or just always go through `record-html-movie.py` which produces
matching outputs.

**Scene visuals start before the audio.** The default `loadScene` adds
a 500ms delay before audio fade-in. Our audio-play marks capture that
delay precisely (the visual mark fires first, then the audio mark 500ms
later), and `adelay` uses the audio-play mark — so this aligns. If you
see audio leading the visuals, you wired your marks to the scene-active
event instead of the audio-play event.

**ARM64 Chromium failures.** Puppeteer's `@puppeteer/browsers install`
hard-codes x86_64 binaries even on aarch64. Use Playwright
(`npx playwright install chromium`) — it has a separate ARM64 build
labelled "fallback build for ubuntu24.04-arm64". The recorder uses
Playwright for exactly this reason.

**Headless chromium can't synthesize the screencast for very tall
content.** If a scene's content overflows 1080px tall, you'll see the
top portion captured and the rest clipped. The clean-mode CSS centres
the scene vertically inside the viewport so this is usually fine — but
re-check overflow with `tools/screenshot-scenes.js` before running the
full record.
