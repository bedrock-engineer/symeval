// Records the live DataFrame/table example (from getting_started.py) into an
// animated GIF: selecting a member row in the marimo.ui.table updates that
// member's axial-stress symbolic evaluation below it.
//
// Playwright clicks each row's selection checkbox (role="checkbox"); the output
// is KaTeX (no iframe), so it re-renders cleanly. A single clip captures the
// table together with the evaluation. Each selection is one frame with a long
// per-frame delay so viewers can read the result.

import { launch, parkMouse } from "./lib/app.mjs";
import { writeGif, loadImage } from "./lib/gif.mjs";
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../docs/public/table.gif");
const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const TEST = process.env.MODE === "test";

const OUT_W = 760;
const STEP_MS = 1100; // time each selected member is shown
const SECTIONS = ["W14x90", "HSS8x8x5/8", "HSS6x6x3/8", "L4x4", "C8x11.5"];

const { browser, page } = await launch({ width: 1200, height: 1200 });
await page.goto(URL, { waitUntil: "networkidle" });
await page.getByText("W14x90", { exact: true }).waitFor({ timeout: 40000 });
await page.waitForTimeout(1500);

const headerCell = page.getByText("member_type", { exact: true });
const heading = page.getByText(/Axial Resistance of a Steel HSS/).first();

await headerCell.scrollIntoViewIfNeeded();
await page.mouse.move(600, 500);
const hb = await headerCell.boundingBox();
await page.mouse.wheel(0, hb.y - 60);
await page.waitForTimeout(400);
const top = (await headerCell.boundingBox()).y;
const bot = (await heading.boundingBox()).y;
const CLIP = { x: 78, y: Math.round(top - 16), width: 984, height: Math.round(bot - 24 - (top - 16)) };
console.log("CLIP", JSON.stringify(CLIP));

const frames = [];
async function shoot(delay) {
  frames.push({ buf: await page.screenshot({ clip: CLIP }), delay });
}
async function selectRow(section) {
  await page.getByText(section, { exact: true }).locator("xpath=ancestor::tr[1]").locator('[role="checkbox"]').click();
  await parkMouse(page, CLIP.x + CLIP.width + 60);
  await page.waitForTimeout(520); // kernel recompute + KaTeX re-render
}

if (TEST) {
  await selectRow("HSS6x6x3/8"); // brace, +69.5 MPa
  await shoot(STEP_MS);
  writeFileSync(resolve(HERE, "../tmp/table-frame.png"), frames.at(-1).buf);
  console.log(`TEST wrote table-frame.png, CLIP height ${CLIP.height}`);
} else {
  for (const s of SECTIONS) { await selectRow(s); await shoot(STEP_MS); }
  await selectRow(SECTIONS[0]); // loop back so the GIF cycles smoothly
  await shoot(STEP_MS);
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
const out = TEST ? resolve(HERE, "../tmp/table-test.gif") : OUT;
const bytes = await writeGif(out, frames, { width: OUT_W, height: OUT_H, draw });
console.log(`wrote ${out}  ${OUT_W}x${OUT_H}  frames=${frames.length}  ${(bytes / 1024).toFixed(0)} KB`);
