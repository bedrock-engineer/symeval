import { chromium } from "playwright";
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 2 });
await page.goto(process.env.APP_URL || "http://127.0.0.1:2821/", { waitUntil: "networkidle" });
const sliders = page.locator('[role="slider"]');
await sliders.first().waitFor({ timeout: 40000 });
await page.waitForTimeout(1500);
// Walk up ancestors of the V thumb (index 1), printing width + class.
let loc = sliders.nth(1);
for (let up = 0; up <= 6; up++) {
  const bb = await loc.boundingBox().catch(() => null);
  const info = await loc.evaluate((el) => ({ tag: el.tagName, cls: (el.getAttribute("class") || "").slice(0, 40), role: el.getAttribute("role") })).catch(() => ({}));
  console.log(`up ${up}: w=${bb ? Math.round(bb.width) : "?"} x=${bb ? Math.round(bb.x) : "?"} <${info.tag} role=${info.role} class="${info.cls}">`);
  loc = loc.locator("xpath=..");
}
await b.close();
