// Records the live ideal-gas piston widget (from the running getting_started.py
// marimo app) into an animated GIF for the README.
//
// Approach: Playwright drives the real marimo sliders. Because debounce=True,
// dragging a handle doesn't update the kernel until release — so we glide the
// handle (capturing frames), release to commit one reactive update, wait for the
// piston iframe to reload, then hold while the piston's own requestAnimationFrame
// animates the gas particles (capturing a smooth burst).
//
// The controls and the piston live in two separate marimo cells with dead space
// between them, so each frame captures two bands (controls, piston+equation) and
// composites them with node-canvas, dropping the gap. gifenc encodes the GIF —
// no ffmpeg, no notebook edits.

import { launch } from "./lib/app.mjs";
import { writeGif, loadImage } from "./lib/gif.mjs";
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../docs/public/piston.gif");
const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const TEST = process.env.MODE === "test";

const FPS = 20;
const DELAY = Math.round(1000 / FPS);
const OUT_W = 620; // final GIF width
const BAND_W = 712; // css width of each captured band
const BAND_X = 188; // css left of each band
const GAP = 12; // px between the two composited bands
const RANGE = { 0: [1, 500], 1: [5, 100], 2: [100, 1000], 3: [0.1, 10] }; // idx: P V T n
const STEP = { 0: 1, 1: 0.5, 2: 1, 3: 0.1 };

const { browser, page } = await launch({ width: 1200, height: 900 });
await page.goto(URL, { waitUntil: "networkidle" });
const sliders = page.locator('[role="slider"]');
await sliders.first().waitFor({ timeout: 40000 });
await page.waitForTimeout(2000);

// marimo scrolls inside its own container (not window): scrollIntoViewIfNeeded +
// wheel to bring the top slider near y=55.
await sliders.nth(0).scrollIntoViewIfNeeded();
await page.mouse.move(600, 400);
let s0 = await sliders.nth(0).boundingBox();
await page.mouse.wheel(0, s0.y - 55);
await page.waitForTimeout(400);
s0 = await sliders.nth(0).boundingBox();
const s3 = await sliders.nth(3).boundingBox();

// Piston iframe: pick the ~290x380 iframe (avoid any other iframes on the page).
const iboxes = await page.locator("iframe").evaluateAll((els) =>
  els.map((e) => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; })
);
const pbox = iboxes.find((b) => b.w > 260 && b.w < 330) || iboxes[0];

// Two capture bands (css viewport coords).
const CLIP_A = { x: BAND_X, y: Math.round(s0.y - 30), width: BAND_W, height: Math.round(s3.y + 46 - (s0.y - 30)) };
const CLIP_B = { x: BAND_X, y: Math.round(pbox.y - 10), width: BAND_W, height: Math.round(pbox.h + 22) };
console.log("CLIP_A", JSON.stringify(CLIP_A), "CLIP_B", JSON.stringify(CLIP_B));

const frames = [];
async function shoot() {
  const a = await page.screenshot({ clip: CLIP_A });
  const c = await page.screenshot({ clip: CLIP_B });
  frames.push({ a, c, delay: DELAY });
}
async function hold(n, gap = 45) {
  for (let i = 0; i < n; i++) { await page.waitForTimeout(gap); await shoot(); }
}
async function clickRadio(text) {
  await page.getByText(text, { exact: true }).first().click();
  await page.waitForTimeout(1000); // solve-for switch: sliders reset + piston reloads
}
async function glide(idx, toValue) {
  const [min, max] = RANGE[idx];
  const track = await sliders.nth(idx).locator("xpath=../..").boundingBox();
  const thumb = await sliders.nth(idx).boundingBox();
  const r = thumb.width / 2;
  const cy = thumb.y + thumb.height / 2;
  const fromX = thumb.x + r;
  const f = Math.max(0, Math.min(1, (toValue - min) / (max - min)));
  const toX = track.x + r + f * (track.width - 2 * r);
  const pxPerUnit = (track.width - 2 * r) / (max - min);
  await page.mouse.move(fromX, cy);
  await page.mouse.down();
  const steps = 12;
  let curX = fromX;
  for (let s = 1; s <= steps; s++) {
    curX = fromX + (toX - fromX) * (s / steps);
    await page.mouse.move(curX, cy);
    await page.waitForTimeout(18);
    await shoot(); // handle glides; piston still shows previous state
  }
  // Precision correction while still held (radix aria-valuenow updates live, so
  // no commit/reload happens until release): nudge onto the exact target.
  for (let k = 0; k < 6; k++) {
    const cur = parseFloat(await sliders.nth(idx).getAttribute("aria-valuenow"));
    if (!Number.isFinite(cur) || Math.abs(toValue - cur) <= STEP[idx]) break;
    curX += (toValue - cur) * pxPerUnit;
    await page.mouse.move(curX, cy);
    await page.waitForTimeout(30);
  }
  await page.mouse.up();
  await page.waitForTimeout(600); // commit -> iframe reload -> first draw (not captured)
  await hold(9); // stable, particles animate
}

if (TEST) {
  await hold(4);
  await glide(1, 80);
  await glide(2, 800);
  await glide(3, 5);
  await glide(3, 7.5); // P -> ~623 kPa > 500 -> 💥 above max
  await hold(10);
  const idxs = [0, frames.length - 1];
  for (const i of idxs) { writeFileSync(resolve(HERE, `../tmp/A-${i}.png`), frames[i].a); writeFileSync(resolve(HERE, `../tmp/B-${i}.png`), frames[i].c); }
  console.log(`TEST captured ${frames.length} frames`);
} else {
  // Phase 1 — solving for P (default). Cranking the inputs pushes P past its
  // 500 kPa max, so the 💥 out-of-bounds indicator appears.
  await hold(8);
  await glide(1, 80); // V -> 80 L
  await glide(2, 800); // T -> 800 K
  await glide(3, 5); // n -> 5 mol  (P ~416 kPa, still in range)
  await glide(3, 7.5); // n -> 7.5 mol  => P ~623 kPa > 500 => 💥
  await hold(18); // linger on the 💥
  // Phase 2 — switch to solving for T (this resets the sliders to defaults).
  await clickRadio("T (K)");
  await hold(8);
  await glide(0, 203); // P -> 203 kPa (2 atm)
  await glide(1, 80); // V -> 80 L
  await glide(3, 10); // n -> 10 mol
  await glide(0, 5); // P -> 5 kPa  => T solved very cold
  await hold(14);
  console.log(`captured ${frames.length} frames`);
}
await browser.close();

// Composite the two bands (controls above, piston+equation below) into one frame.
const SCALE = OUT_W / BAND_W;
const topH = Math.round(CLIP_A.height * SCALE);
const botH = Math.round(CLIP_B.height * SCALE);
const OUT_H = topH + GAP + botH;
const draw = async (ctx, { a, c }) => {
  const ia = await loadImage(a);
  const ic = await loadImage(c);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, OUT_W, OUT_H);
  ctx.drawImage(ia, 0, 0, OUT_W, topH);
  ctx.drawImage(ic, 0, topH + GAP, OUT_W, botH);
};
const out = TEST ? resolve(HERE, "../tmp/piston-test.gif") : OUT;
const bytes = await writeGif(out, frames, { width: OUT_W, height: OUT_H, draw });
console.log(`wrote ${out}  ${OUT_W}x${OUT_H}  frames=${frames.length}  ${(bytes / 1024).toFixed(0)} KB`);
