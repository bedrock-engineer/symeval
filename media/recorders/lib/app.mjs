// Shared browser helpers for the README recorders.

import { chromium } from "playwright";

/**
 * Launch headless Chromium and open a page at the given viewport / device scale.
 * @returns `{ browser, page }` — the caller closes `browser` when done.
 */
export async function launch({ width = 1200, height = 900, scale = 2 } = {}) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: scale });
  return { browser, page };
}

/** Move the cursor out of the captured region so no element shows a hover state. */
export const parkMouse = (page, x, y = 12) => page.mouse.move(x, y);
