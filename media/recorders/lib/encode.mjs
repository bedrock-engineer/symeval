// Shared multi-format encoding for the README/promo recorders.
//
// One frame array in, three files out:
//   .gif  — downscaled, palettized (gifenc), keeps per-frame `delay` timing.
//   .mp4  — full capture resolution, H.264 (ffmpeg libx264), constant fps.
//   .webp — full capture resolution, animated (ffmpeg libwebp), constant fps.
//
// The recorders capture frames with variable per-frame holds (`delay`, in ms).
// The GIF honours those delays directly. The video formats need a constant fps,
// so each frame is repeated round(delay/1000 * fps) times into the stream. Each
// unique frame is drawn once and its RGBA buffer written N times to ffmpeg's
// rawvideo stdin — no re-render, no intermediate PNGs on disk.

import { loadImage, createCanvas } from "canvas";
import gifenc from "gifenc";
import ffmpegPath from "ffmpeg-static";
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync, statSync, mkdtempSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";

const { GIFEncoder, quantize, applyPalette } = gifenc;

export { loadImage };

const even = (n) => 2 * Math.round(n / 2);

/**
 * Encode `frames` to `.gif`, `.mp4` and `.webp` beside each other.
 *
 * @param outBase  Absolute output path without extension (parent dirs created).
 * @param frames   Array of `{ delay, ...payload }`; `delay` is the per-frame hold
 *                 in ms, `payload` is whatever `draw` needs (e.g. screenshots).
 * @param opts.gif   `{ width, height }` — downscaled GIF dimensions.
 * @param opts.full  `{ width, height }` — full-res dimensions for mp4/webp
 *                   (rounded to even for yuv420p). Defaults to `gif` dims.
 * @param opts.draw  `async (ctx, frame, W, H) => void` — paints one frame onto a
 *                   W×H canvas from its payload.
 * @param opts.fps   Constant frame rate for mp4/webp (default 30).
 * @param opts.formats  Subset of `["gif", "mp4", "webp"]` (default all three).
 * @param opts.webpWidth  Downscale the webp to this width (default = full width).
 *                 Dense clips (the piston) need a smaller webp to stay reasonable.
 * @param opts.webpQuality  libwebp `-q:v` 0-100 (default 80). Lower for dense clips.
 * @returns  `{ gif?, mp4?, webp? }` byte sizes for the formats written.
 */
export async function writeClips(outBase, frames, { gif, full, draw, fps = 30, formats = ["gif", "mp4", "webp"], webpWidth, webpQuality = 80 }) {
  full = full ? { width: even(full.width), height: even(full.height) } : { width: even(gif.width), height: even(gif.height) };
  mkdirSync(dirname(outBase), { recursive: true });
  const sizes = {};

  if (formats.includes("gif")) {
    sizes.gif = await writeGif(`${outBase}.gif`, frames, { width: gif.width, height: gif.height, draw });
  }

  if (formats.includes("mp4") || formats.includes("webp")) {
    // Draw each unique frame once at full res to a PNG still, then let ffmpeg's
    // concat demuxer hold each for its `delay`. Encoding only unique frames (not
    // fps-expanded duplicates) keeps the animated webp small — repeating static
    // holds as real frames balloons libwebp output by ~100x.
    const dir = mkdtempSync(join(tmpdir(), "symeval-clip-"));
    try {
      const canvas = createCanvas(full.width, full.height);
      const ctx = canvas.getContext("2d");
      const lines = [];
      let last;
      for (let i = 0; i < frames.length; i++) {
        await draw(ctx, frames[i], full.width, full.height);
        last = join(dir, `f${i}.png`);
        writeFileSync(last, canvas.toBuffer("image/png"));
        lines.push(`file '${last}'`, `duration ${((frames[i].delay ?? 1000 / fps) / 1000).toFixed(4)}`);
      }
      lines.push(`file '${last}'`); // repeat last so its duration is honoured
      const list = join(dir, "list.txt");
      writeFileSync(list, lines.join("\n"));

      // mp4: resample the variable-duration stream to constant fps for smooth
      // playback; h264 dedupes the static holds cheaply.
      if (formats.includes("mp4")) sizes.mp4 = await ffmpegConcat(list, `${outBase}.mp4`, [
        "-vsync", "cfr", "-r", String(fps),
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart",
      ]);
      // webp: keep the variable per-frame durations (like the gif); optionally
      // downscale from the full-res stills for dense clips.
      if (formats.includes("webp")) {
        const scale = webpWidth && webpWidth !== full.width ? ["-vf", `scale=${webpWidth}:-2:flags=lanczos`] : [];
        sizes.webp = await ffmpegConcat(list, `${outBase}.webp`, [
          ...scale, "-an", "-c:v", "libwebp", "-lossless", "0", "-q:v", String(webpQuality), "-loop", "0",
        ]);
      }
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  }

  return sizes;
}

/** Encode a concat-demuxer still list to `out`. Returns byte size. */
function ffmpegConcat(list, out, encodeArgs) {
  const args = ["-y", "-f", "concat", "-safe", "0", "-i", list, ...encodeArgs, out];
  return new Promise((resolve, reject) => {
    const ff = spawn(ffmpegPath, args, { stdio: ["ignore", "ignore", "pipe"] });
    let err = "";
    ff.stderr.on("data", (d) => (err += d));
    ff.on("error", reject);
    ff.on("close", (code) => (code === 0 ? resolve(statSync(out).size) : reject(new Error(`ffmpeg ${code}: ${err.slice(-800)}`))));
  });
}

/** Encode `frames` to a palettized GIF at `out` (global palette, per-frame delays). */
async function writeGif(out, frames, { width, height, draw }) {
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");
  const toRGBA = async (frame) => {
    await draw(ctx, frame, width, height);
    return ctx.getImageData(0, 0, width, height).data;
  };

  // Global palette sampled evenly across the timeline so transient colours survive.
  const n = Math.min(8, frames.length);
  const samples = [];
  for (let i = 0; i < n; i++) {
    samples.push(await toRGBA(frames[Math.floor((i / Math.max(1, n - 1)) * (frames.length - 1))]));
  }
  const merged = new Uint8ClampedArray(samples.reduce((a, d) => a + d.length, 0));
  {
    let o = 0;
    for (const d of samples) { merged.set(d, o); o += d.length; }
  }
  const palette = quantize(merged, 256);

  const gif = GIFEncoder();
  for (const frame of frames) {
    gif.writeFrame(applyPalette(await toRGBA(frame), palette), width, height, { palette, delay: frame.delay });
  }
  gif.finish();

  const bytes = gif.bytes();
  writeFileSync(out, bytes);
  return bytes.length;
}
