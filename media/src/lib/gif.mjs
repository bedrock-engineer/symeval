// Shared GIF encoding for the README recorders.
//
// node-canvas composites/downscales each frame; gifenc encodes. A single global
// palette is sampled across the whole timeline so transient colours (e.g. the
// piston's hot-red particles) survive quantization. No ffmpeg involved.

import { loadImage, createCanvas } from "canvas";
import gifenc from "gifenc";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

const { GIFEncoder, quantize, applyPalette } = gifenc;

export { loadImage };

/**
 * Encode `frames` to a GIF at `out`.
 *
 * @param out     Absolute output path (parent dirs are created).
 * @param frames  Array of `{ delay, ...payload }`; `delay` is the per-frame hold
 *                in milliseconds, `payload` is whatever `draw` needs.
 * @param width   Output width in px.
 * @param height  Output height in px.
 * @param draw    `async (ctx, frame) => void` — paints one frame onto the
 *                width×height canvas from its payload (e.g. screenshot buffers).
 * @returns       Encoded byte length.
 */
export async function writeGif(out, frames, { width, height, draw }) {
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");
  const toRGBA = async (frame) => {
    await draw(ctx, frame);
    return ctx.getImageData(0, 0, width, height).data;
  };

  // Global palette sampled evenly across the timeline.
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

  mkdirSync(dirname(out), { recursive: true });
  const bytes = gif.bytes();
  writeFileSync(out, bytes);
  return bytes.length;
}
