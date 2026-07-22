import { chromium } from "playwright";

const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 2 });
await page.goto(URL, { waitUntil: "networkidle" });

const sliders = page.locator('[role="slider"]');
await sliders.first().waitFor({ timeout: 40000 });
await page.waitForTimeout(1500);

// Position each slider + the piston iframe (Playwright boundingBox pierces shadow DOM).
const n = await sliders.count();
for (let i = 0; i < n; i++) {
  const bb = await sliders.nth(i).boundingBox();
  console.log(`slider ${i}:`, bb && { x: Math.round(bb.x), y: Math.round(bb.y), w: Math.round(bb.width), h: Math.round(bb.height) });
}
const iframe = page.locator("iframe").first();
console.log("iframe:", await iframe.boundingBox());

// Bring the first slider near the top, then shoot the whole viewport to see layout.
await sliders.first().scrollIntoViewIfNeeded();
await page.evaluate(() => window.scrollBy(0, -40));
await page.waitForTimeout(400);
await page.screenshot({ path: "tmp/region.png" });
console.log("wrote tmp/region.png");
await b.close();
