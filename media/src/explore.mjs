import { chromium } from "playwright";

const URL = process.env.APP_URL || "http://127.0.0.1:2821/";
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1400, height: 1100 }, deviceScaleFactor: 2 });
await page.goto(URL, { waitUntil: "networkidle" });
await page.waitForTimeout(6000);

await page.screenshot({ path: "tmp/full.png", fullPage: true });

const summarize = (sel, extra = () => ({})) =>
  page.$$eval(sel, (els, extraStr) => {
    const fn = new Function("el", `return (${extraStr})(el)`);
    return els.map((el, i) => {
      const r = el.getBoundingClientRect();
      return { i, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), ...fn(el) };
    });
  }, extra.toString());

console.log("INPUTS:", JSON.stringify(await summarize("input", (el) => ({ type: el.type, value: el.value, min: el.min, max: el.max, step: el.step })), null, 2));
console.log("ROLE=slider:", JSON.stringify(await summarize('[role="slider"]', (el) => ({ aria: el.getAttribute("aria-valuenow") })), null, 2));
console.log("RADIO labels:", JSON.stringify(await page.$$eval('input[type="radio"]', (els) => els.map((el) => ({ checked: el.checked, label: el.closest("label")?.innerText || el.parentElement?.innerText }))), null, 2));
console.log("IFRAMES:", JSON.stringify(await summarize("iframe", (el) => ({ hasSrcdoc: el.hasAttribute("srcdoc"), src: (el.getAttribute("src") || "").slice(0, 30) })), null, 2));
console.log("PAGE HEIGHT:", await page.evaluate(() => document.body.scrollHeight));
await b.close();
