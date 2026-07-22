// Records the live HSS axial-resistance example (from getting_started.py) into an
// animated GIF: sweeping the Beam length L ripples through the whole chained
// check F_e -> lambda -> C_r -> DCR, with the full input table visible.
//
// Playwright drives the real `Beam length` mo.ui.number input. Outputs are KaTeX
// (no iframe), so each change re-renders cleanly. A single tall clip captures the
// entire input table together with the four equations. Each L value is a single
// frame with a long per-frame delay, so the file stays small while giving the
// viewer time to read each state. node-canvas downscales, gifenc encodes.

import { launch, parkMouse } from "./lib/app.mjs";
import { writeGif, loadImage } from "./lib/gif.mjs";
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../docs/public/hss.gif");
const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const TEST = process.env.MODE === "test";

const OUT_W = 620;
const STEP_MS = 600; // time each L value is shown
const HOLD_MS = 1500; // time the endpoints linger

const { browser, page } = await launch({ width: 1200, height: 1300 });
await page.goto(URL, { waitUntil: "networkidle" });
await page.getByText("Beam length", { exact: true }).waitFor({ timeout: 40000 });
await page.waitForTimeout(1500);

const beamInput = page.getByText("Beam length", { exact: true }).locator("xpath=ancestor::tr[1]").locator("input");
const table = page.getByText("Beam length", { exact: true }).locator("xpath=ancestor::table[1]");
const eulerLabel = page.getByText("Euler buckling stress", { exact: true });
const dcrLabel = page.getByText("Demand capacity ratio", { exact: true });

// Scroll the input table near the top so the whole table + equations fit in one
// tall viewport, then build a single clip spanning table-top -> DCR-bottom.
await table.scrollIntoViewIfNeeded();
await page.mouse.move(600, 500);
let tb = await table.boundingBox();
await page.mouse.wheel(0, tb.y - 40);
await page.waitForTimeout(400);

tb = await table.boundingBox();
const eb = await eulerLabel.boundingBox();
const db = await dcrLabel.boundingBox();
const left = Math.min(tb.x, eb.x);
const top = Math.round(tb.y - 12);
const CLIP = {
  x: Math.round(left - 8),
  y: top,
  width: Math.round(Math.max(tb.x + tb.width, eb.x + 640) - left + 16),
  height: Math.round(db.y + db.height - top + 20),
};
console.log("CLIP", JSON.stringify(CLIP));

const frames = [];
async function shoot(delay) {
  frames.push({ buf: await page.screenshot({ clip: CLIP }), delay });
}
async function setL(v) {
  await beamInput.fill(String(v)); // Playwright clicks the input (moves cursor in)
  await beamInput.press("Enter");
  await parkMouse(page, CLIP.x + CLIP.width + 60);
  await page.waitForTimeout(460); // kernel recompute + KaTeX re-render
}

const sweep = [];
for (let v = 4; v <= 12.001; v += 1) sweep.push(v);

if (TEST) {
  await setL(4);
  await shoot(STEP_MS);
  writeFileSync(resolve(HERE, `../tmp/hss-frame.png`), frames.at(-1).buf);
  console.log(`TEST wrote hss-frame.png, CLIP height ${CLIP.height}`);
} else {
  await setL(6.5);
  await shoot(HOLD_MS); // default
  for (const v of sweep) { await setL(v); await shoot(STEP_MS); } // sweep up, watch it ripple
  await shoot(HOLD_MS); // linger at the slender end (DCR > 1, member fails)
  await setL(6.5);
  await shoot(HOLD_MS); // back to default
  console.log(`captured ${frames.length} frames`);
}
await browser.close();

const OUT_H = Math.round((OUT_W * CLIP.height) / CLIP.width);
const draw = async (ctx, { buf }) => {
  const img = await loadImage(buf);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, OUT_W, OUT_H);
  ctx.drawImage(img, 0, 0, OUT_W, OUT_H);
};
const out = TEST ? resolve(HERE, "../tmp/hss-test.gif") : OUT;
const bytes = await writeGif(out, frames, { width: OUT_W, height: OUT_H, draw });
console.log(`wrote ${out}  ${OUT_W}x${OUT_H}  frames=${frames.length}  ${(bytes / 1024).toFixed(0)} KB`);
