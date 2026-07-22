// Export share-friendly still-image versions of the promo from the rendered mp4:
//   symeval-promo.gif  — universal (email, chat), palette-optimised.
//   symeval-promo.webp — animated, ~1.4x the gif's resolution at the same size.
//
// mp4 stays the primary (docs <video>, social). Run after `npm run promo`.
// Defaults target ~6 MB each; override via env (GIF_W, WEBP_W, WEBP_Q, ...).

import ffmpegPath from "ffmpeg-static";
import { spawn } from "node:child_process";
import { statSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const MP4 = resolve(HERE, "../../docs/public/symeval-promo.mp4");
const GIF = resolve(HERE, "../../docs/public/symeval-promo.gif");
const WEBP = resolve(HERE, "../../docs/public/symeval-promo.webp");
const PAL = resolve(HERE, "../tmp/promo-palette.png");

const GIF_W = +(process.env.GIF_W ?? 900);
const GIF_FPS = +(process.env.GIF_FPS ?? 15);
const WEBP_W = +(process.env.WEBP_W ?? 1280);
const WEBP_FPS = +(process.env.WEBP_FPS ?? 15);
const WEBP_Q = +(process.env.WEBP_Q ?? 46);

const run = (args) =>
  new Promise((res, rej) => {
    const ff = spawn(ffmpegPath, ["-hide_banner", "-loglevel", "error", "-y", ...args], { stdio: ["ignore", "ignore", "pipe"] });
    let err = "";
    ff.stderr.on("data", (d) => (err += d));
    ff.on("error", rej);
    ff.on("close", (c) => (c === 0 ? res() : rej(new Error(`ffmpeg ${c}: ${err.slice(-600)}`))));
  });

const mb = (p) => (statSync(p).size / 1048576).toFixed(2);

if (!statSync(MP4, { throwIfNoEntry: false })) {
  console.error(`No ${MP4} — run \`npm run promo\` first.`);
  process.exit(1);
}
mkdirSync(dirname(PAL), { recursive: true });

// gif — two-pass palette for decent quality at 256 colours.
const gifChain = `fps=${GIF_FPS},scale=${GIF_W}:-1:flags=lanczos`;
await run(["-i", MP4, "-vf", `${gifChain},palettegen=stats_mode=diff`, PAL]);
await run(["-i", MP4, "-i", PAL, "-lavfi", `${gifChain}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3`, GIF]);
console.log(`wrote symeval-promo.gif   ${GIF_W}px@${GIF_FPS}fps        ${mb(GIF)} MB`);

// webp — animated, higher res than the gif for the same size budget.
await run(["-i", MP4, "-vf", `fps=${WEBP_FPS},scale=${WEBP_W}:-1:flags=lanczos`, "-c:v", "libwebp", "-lossless", "0", "-q:v", String(WEBP_Q), "-loop", "0", "-an", WEBP]);
console.log(`wrote symeval-promo.webp  ${WEBP_W}px@${WEBP_FPS}fps q${WEBP_Q}    ${mb(WEBP)} MB`);
