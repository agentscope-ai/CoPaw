#!/usr/bin/env node
/**
 * record-html-movie.js — drive Chromium via Playwright + CDP screencast
 * to capture an HTML "movie demo" into a frames directory and a marks
 * JSON. Audio is muted in the browser; the Python wrapper builds the
 * audio track from per-scene mp3 files at the captured marks.
 *
 * Usage:
 *   node record-html-movie.js \
 *        --url file:///abs/path/demo.html?clean=1 \
 *        --frames /tmp/frames \
 *        --marks  /tmp/marks.json \
 *        --width  1920 --height 1080 --quality 88
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return (i >= 0 && i + 1 < process.argv.length) ? process.argv[i + 1] : def;
}

const URL_       = arg('url');
const FRAMES_DIR = arg('frames');
const MARKS_PATH = arg('marks');
const WIDTH      = parseInt(arg('width', '1920'));
const HEIGHT     = parseInt(arg('height', '1080'));
const QUALITY    = parseInt(arg('quality', '88'));
const DPR        = parseFloat(arg('dpr', '1'));   // deviceScaleFactor
const MAX_SECS   = parseInt(arg('max-secs', '1500')); // hard ceiling

if (!URL_ || !FRAMES_DIR || !MARKS_PATH) {
  console.error('Missing --url / --frames / --marks');
  process.exit(2);
}
fs.mkdirSync(FRAMES_DIR, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--autoplay-policy=no-user-gesture-required',
      '--mute-audio',
      '--hide-scrollbars',
      `--window-size=${WIDTH},${HEIGHT}`,
    ],
  });
  const context = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    deviceScaleFactor: DPR,
  });
  const page = await context.newPage();

  await page.goto(URL_, { waitUntil: 'load', timeout: 60_000 });
  await page.waitForFunction('window.__movieReady === true', null, { timeout: 30_000 });
  // Give the first scene a moment to settle (audioFadeIn 500ms delay).
  await page.waitForTimeout(800);

  const client = await context.newCDPSession(page);

  let frameIdx = 0;
  const t0 = Date.now() / 1000;
  const pending = [];

  client.on('Page.screencastFrame', (params) => {
    const seq = ++frameIdx;
    const name = String(seq).padStart(6, '0');
    const ts = (Date.now() / 1000) - t0;
    pending.push((async () => {
      await fs.promises.writeFile(path.join(FRAMES_DIR, `${name}.jpg`), Buffer.from(params.data, 'base64'));
      await fs.promises.writeFile(path.join(FRAMES_DIR, `${name}.t`),  ts.toFixed(6));
    })());
    client.send('Page.screencastFrameAck', { sessionId: params.sessionId })
      .catch(() => {});  // session may close during shutdown
  });

  // At deviceScaleFactor > 1 we want the screencast to capture the
  // rendered pixel resolution (WIDTH*DPR × HEIGHT*DPR), not the logical
  // viewport — that's the whole point of supersampling capture.
  const captureW = Math.round(WIDTH  * DPR);
  const captureH = Math.round(HEIGHT * DPR);
  await client.send('Page.startScreencast', {
    format: 'jpeg',
    quality: QUALITY,
    maxWidth:  captureW,
    maxHeight: captureH,
    everyNthFrame: 1,
  });

  const deadline = Date.now() + MAX_SECS * 1000;
  while (Date.now() < deadline) {
    const done = await page.evaluate('window.__movieDone === true').catch(() => false);
    if (done) break;
    await page.waitForTimeout(500);
  }
  // 1.5s tail so the last frame settles.
  await page.waitForTimeout(1500);
  await client.send('Page.stopScreencast').catch(() => {});

  // Flush remaining file writes
  await Promise.all(pending);

  const marks = await page.evaluate('window.__movieMarks');
  const tEnd  = (Date.now() / 1000) - t0;
  fs.writeFileSync(MARKS_PATH, JSON.stringify({
    marks: marks || [],
    startedAt: 0,
    endedAt: tEnd,
    frameCount: frameIdx,
    width: WIDTH,
    height: HEIGHT,
  }, null, 2));

  console.log(`captured ${frameIdx} frames, duration=${tEnd.toFixed(1)}s`);
  await browser.close();
})().catch(e => {
  console.error(e);
  process.exit(1);
});
