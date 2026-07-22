import { chromium } from "playwright";

const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 2 });
await page.goto(URL, { waitUntil: "networkidle" });

const sliders = page.locator('[role="slider"]');
await sliders.first().waitFor({ timeout: 40000 });
await page.waitForTimeout(1500);

// Track geometry: the thumb's parent is the track. Report both.
for (let i = 0; i < 4; i++) {
  const thumb = await sliders.nth(i).boundingBox();
  const track = await sliders.nth(i).locator("xpath=..").boundingBox();
  console.log(`slider ${i}: thumb x=${Math.round(thumb.x)} | track x=${Math.round(track.x)} w=${Math.round(track.width)}`);
}

// Drag the V slider (index 1) to the right and see if the equation/piston react.
await sliders.nth(1).scrollIntoViewIfNeeded();
await page.evaluate(() => window.scrollBy(0, -120));
await page.waitForTimeout(300);

const thumb = await sliders.nth(1).boundingBox();
const track = await sliders.nth(1).locator("xpath=..").boundingBox();
const cy = thumb.y + thumb.height / 2;
const targetX = track.x + track.width * 0.7; // ~70% of V range
await page.mouse.move(thumb.x + thumb.width / 2, cy);
await page.mouse.down();
for (let s = 1; s <= 20; s++) {
  const x = thumb.x + thumb.width / 2 + (targetX - (thumb.x + thumb.width / 2)) * (s / 20);
  await page.mouse.move(x, cy);
  await page.waitForTimeout(12);
}
await page.mouse.up();
await page.waitForTimeout(1500); // let debounce + kernel update land

// Report the V number input value and screenshot.
const numbers = page.locator('input[type="text"]');
const vals = [];
const cnt = await numbers.count();
for (let i = 0; i < cnt; i++) vals.push(await numbers.nth(i).inputValue().catch(() => "?"));
console.log("text input values after drag:", vals);
await page.screenshot({ path: "tmp/after-drag.png" });
console.log("wrote tmp/after-drag.png");
await b.close();
