// Records the live HSS axial-resistance example (from getting_started.py) into an
// animated GIF: sweeping the Beam length L ripples through the whole chained
// check F_e -> lambda -> C_r -> DCR.
//
// Playwright drives the real `Beam length` mo.ui.number input. These outputs are
// KaTeX (no iframe), so each change re-renders cleanly with no reload. Each frame
// composites two bands (the Beam length row + the four equations), dropping the
// rest of the input table between them. node-canvas composites, gifenc encodes.

import { chromium } from "playwright";
import { loadImage, createCanvas } from "canvas";
import gifenc from "gifenc";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const { GIFEncoder, quantize, applyPalette } = gifenc;

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../docs/public/hss.gif");
const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const TEST = process.env.MODE === "test";

const FPS = 16;
const OUT_W = 640;
const BAND_X = 232;
const BAND_W = 650;
const GAP = 14;

const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: 2 });
await page.goto(URL, { waitUntil: "networkidle" });
await page.getByText("Beam length", { exact: true }).waitFor({ timeout: 40000 });
await page.waitForTimeout(1500);

const beamInput = page.getByText("Beam length", { exact: true }).locator("xpath=ancestor::tr[1]").locator("input");
const beamRow = page.getByText("Beam length", { exact: true }).locator("xpath=ancestor::tr[1]");
const eulerLabel = page.getByText("Euler buckling stress", { exact: true });
const dcrLabel = page.getByText("Demand capacity ratio", { exact: true });

// Scroll the Beam length row near the top; the equations sit ~450px below and
// still fit in the 1000px viewport.
await beamInput.scrollIntoViewIfNeeded();
await page.mouse.move(600, 500);
let rb = await beamRow.boundingBox();
await page.mouse.wheel(0, rb.y - 45);
await page.waitForTimeout(400);

rb = await beamRow.boundingBox();
const eb = await eulerLabel.boundingBox();
const db = await dcrLabel.boundingBox();
const CLIP_A = { x: BAND_X, y: Math.round(rb.y - 8), width: BAND_W, height: Math.round(rb.height + 16) };
const CLIP_B = { x: BAND_X, y: Math.round(eb.y - 12), width: BAND_W, height: Math.round(db.y + db.height - eb.y + 24) };
console.log("CLIP_A", JSON.stringify(CLIP_A), "CLIP_B", JSON.stringify(CLIP_B));

const frames = [];
async function shoot(n = 1) {
  const a = await page.screenshot({ clip: CLIP_A });
  const c = await page.screenshot({ clip: CLIP_B });
  for (let i = 0; i < n; i++) frames.push({ a, c });
}
async function setL(v) {
  await beamInput.fill(String(v));
  await beamInput.press("Enter");
  await page.waitForTimeout(480); // kernel recompute + KaTeX re-render
}

const sweep = [];
for (let v = 4; v <= 12.001; v += 0.5) sweep.push(Math.round(v * 10) / 10);

if (TEST) {
  await setL(4);
  await shoot();
  await setL(8);
  await shoot();
  await setL(12);
  await shoot();
  writeFileSync(resolve(HERE, `../tmp/hssA.png`), frames.at(-1).a);
  writeFileSync(resolve(HERE, `../tmp/hssB-4.png`), frames[0].c);
  writeFileSync(resolve(HERE, `../tmp/hssB-12.png`), frames.at(-1).c);
  console.log(`TEST frames ${frames.length}`);
} else {
  await setL(6.5);
  await shoot(6); // hold at default
  await setL(4);
  await shoot(6); // stocky beam, low DCR
  for (const v of sweep) { await setL(v); await shoot(2); } // sweep up: watch it ripple
  await shoot(12); // hold at the long/slender end (DCR > 1, member fails)
  await setL(6.5);
  await shoot(8);
  console.log(`captured ${frames.length} frames`);
}
await b.close();

// ---- composite + encode -----------------------------------------------------
const SCALE = OUT_W / BAND_W;
const topH = Math.round(CLIP_A.height * SCALE);
const botH = Math.round(CLIP_B.height * SCALE);
const OUT_H = topH + GAP + botH;
const canvas = createCanvas(OUT_W, OUT_H);
const ctx = canvas.getContext("2d");
async function rgba({ a, c }) {
  const ia = await loadImage(a);
  const ic = await loadImage(c);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, OUT_W, OUT_H);
  ctx.drawImage(ia, 0, 0, OUT_W, topH);
  ctx.drawImage(ic, 0, topH + GAP, OUT_W, botH);
  return ctx.getImageData(0, 0, OUT_W, OUT_H).data;
}
const nSamp = Math.min(8, frames.length);
const merged = [];
for (let i = 0; i < nSamp; i++) merged.push(await rgba(frames[Math.floor((i / (nSamp - 1)) * (frames.length - 1))]));
const all = new Uint8ClampedArray(merged.reduce((a, d) => a + d.length, 0));
{ let o = 0; for (const d of merged) { all.set(d, o); o += d.length; } }
const palette = quantize(all, 256);

const gif = GIFEncoder();
const delay = Math.round(1000 / FPS);
for (const fr of frames) gif.writeFrame(applyPalette(await rgba(fr), palette), OUT_W, OUT_H, { palette, delay });
gif.finish();

for (const i of [Math.floor(frames.length * 0.5)]) { await rgba(frames[i]); writeFileSync(resolve(HERE, `../tmp/hss-preview.png`), canvas.toBuffer("image/png")); }

const out = TEST ? resolve(HERE, "../tmp/hss-test.gif") : OUT;
mkdirSync(dirname(out), { recursive: true });
const bytes = gif.bytes();
writeFileSync(out, bytes);
console.log(`wrote ${out}  ${OUT_W}x${OUT_H}  frames=${frames.length}  ${(bytes.length / 1024).toFixed(0)} KB`);
