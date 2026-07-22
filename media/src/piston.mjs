// Renders the ideal-gas piston widget to an animated GIF for the README.
//
// This is a faithful port of the Canvas-2D animation in symeval_mo.py
// (`piston_js`): same cylinder, weight block, ring handle and bouncing
// particles, same geometry constants. The only additions are (1) a small HUD in
// the cylinder's top margin showing the current P, V, T, n, and (2) a scripted
// sweep of each variable so a static reader sees what every input does.
//
// No browser and no ffmpeg: node-canvas (Cairo) draws each frame, gifenc
// encodes the GIF.

import { createCanvas } from "canvas";
import { GIFEncoder, quantize, applyPalette } from "gifenc";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../docs/assets/gifs/piston.gif");

// ---- logical canvas + geometry (matches symeval_mo.py) ----------------------
const W = 270;
const H = 360;
const SCALE = 2; // render at 2x for crisp text, GIF stays 540x720
const CYL_X = 70;
const CYL_W = 130;
const TOP_MARGIN = 110;
const BOTTOM_MARGIN = 20;
const CYL_BOTTOM = H - BOTTOM_MARGIN;

// ---- slider ranges (mo.ui.slider start/stop in symeval_mo.py) ---------------
const V_MIN = 5, V_MAX = 100;
const P_MIN = 1, P_MAX = 500;
const T_MIN = 100, T_MAX = 1000;
const N_MIN = 0.1, N_MAX = 10;

// default values (mo.ui.slider `value=`)
const DEFAULTS = { P: 101.325, V: 22.4, T: 273.15, n: 1.0 };

const FPS = 20;
const GREEN = "#63805e"; // Bedrock accent, used to highlight the active input

// ---- animation timeline -----------------------------------------------------
// Each segment sweeps one variable out to an extreme and back, easing in/out,
// while the HUD highlights that variable. Holds bookend the loop so it reads
// cleanly when repeated.
const smooth = (t) => t * t * (3 - 2 * t); // smoothstep
const ease = (a, b, t) => a + (b - a) * smooth(Math.max(0, Math.min(1, t)));

function buildTimeline() {
  const frames = [];
  const hold = (n, active = null) => {
    for (let i = 0; i < n; i++) frames.push({ ...DEFAULTS, active });
  };
  // sweep `key` default -> peak -> default over `dur` frames each leg
  const sweep = (key, peak, dur) => {
    for (let i = 0; i < dur; i++) {
      frames.push({ ...DEFAULTS, [key]: ease(DEFAULTS[key], peak, i / dur), active: key });
    }
    for (let i = 0; i < dur; i++) {
      frames.push({ ...DEFAULTS, [key]: ease(peak, DEFAULTS[key], i / dur), active: key });
    }
  };
  hold(18);
  sweep("V", 92, 34); // piston rises, then falls
  hold(10, "V");
  sweep("P", 460, 34); // weight block grows, then shrinks
  hold(10, "P");
  sweep("T", 960, 40); // particles speed up + warm, then slow + cool
  hold(10, "T");
  sweep("n", 9, 34); // more particles, then fewer
  hold(22);
  return frames;
}

// ---- particle system (persists across frames) -------------------------------
const particles = [];
function syncParticleCount(target, pistonY, gasHeight) {
  while (particles.length < target) {
    const ang = Math.random() * Math.PI * 2;
    particles.push({
      x: CYL_X + 4 + Math.random() * (CYL_W - 8),
      y: pistonY + 4 + Math.random() * Math.max(1, gasHeight - 8),
      vx: Math.cos(ang),
      vy: Math.sin(ang),
    });
  }
  if (particles.length > target) particles.length = target;
}

// ---- draw a single frame ----------------------------------------------------
function drawFrame(ctx, s) {
  const { P, V, T, n, active } = s;

  const v01 = Math.max(0, Math.min(1, (V - V_MIN) / (V_MAX - V_MIN)));
  const p01 = Math.max(0, Math.min(1, (P - P_MIN) / (P_MAX - P_MIN)));
  const t01 = Math.max(0, Math.min(1, (T - T_MIN) / (T_MAX - T_MIN)));
  const n01 = Math.max(0, Math.min(1, (n - N_MIN) / (N_MAX - N_MIN)));

  const GAS_MIN = 10;
  const GAS_MAX = H - TOP_MARGIN - BOTTOM_MARGIN;
  const gasHeight = GAS_MIN + v01 * (GAS_MAX - GAS_MIN);
  const pistonY = CYL_BOTTOM - gasHeight;

  const WEIGHT_W_MIN = 40, WEIGHT_W_MAX = CYL_W - 6;
  const WEIGHT_H_MIN = 18, WEIGHT_H_MID = 45, WEIGHT_H_MAX = 90;
  const PHASE_SPLIT = 0.5;
  let weightWBottom, weightH;
  if (p01 <= PHASE_SPLIT) {
    const k = p01 / PHASE_SPLIT;
    weightWBottom = WEIGHT_W_MIN + k * (WEIGHT_W_MAX - WEIGHT_W_MIN);
    weightH = WEIGHT_H_MIN + k * (WEIGHT_H_MID - WEIGHT_H_MIN);
  } else {
    const k = (p01 - PHASE_SPLIT) / (1 - PHASE_SPLIT);
    weightWBottom = WEIGHT_W_MAX;
    weightH = WEIGHT_H_MID + k * (WEIGHT_H_MAX - WEIGHT_H_MID);
  }
  const weightWTop = weightWBottom * 0.55;

  const speed = Math.sqrt(T) * 0.11;
  const tintR = Math.round(80 + t01 * (240 - 80));
  const tintG = Math.round(140 - t01 * 80);
  const tintB = Math.round(240 - t01 * 200);
  const tint = `rgb(${tintR},${tintG},${tintB})`;

  const N_PARTICLES_MIN = 4, N_PARTICLES_MAX = 250;
  const nParticles = Math.max(N_PARTICLES_MIN, Math.min(N_PARTICLES_MAX, Math.round(n01 * N_PARTICLES_MAX)));
  syncParticleCount(nParticles, pistonY, gasHeight);

  // background
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, W, H);

  drawHud(ctx, s);

  // cylinder walls
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(CYL_X, TOP_MARGIN);
  ctx.lineTo(CYL_X, CYL_BOTTOM);
  ctx.lineTo(CYL_X + CYL_W, CYL_BOTTOM);
  ctx.lineTo(CYL_X + CYL_W, TOP_MARGIN);
  ctx.stroke();

  // weight block (trapezoid)
  const cx = CYL_X + CYL_W / 2;
  const wBL = cx - weightWBottom / 2;
  const wBR = cx + weightWBottom / 2;
  const wTL = cx - weightWTop / 2;
  const wTR = cx + weightWTop / 2;
  const wBY = pistonY - 4;
  const wTY = wBY - weightH;
  ctx.fillStyle = "#5a5a5a";
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(wBL, wBY);
  ctx.lineTo(wBR, wBY);
  ctx.lineTo(wTR, wTY);
  ctx.lineTo(wTL, wTY);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // ring handle
  const ringOuterR = 5 + p01 * 6;
  const ringThickness = 2.5 + p01 * 3;
  const ringInnerR = Math.max(1, ringOuterR - ringThickness);
  const ringCenterY = wTY - ringOuterR + 2;
  ctx.fillStyle = "#333";
  ctx.beginPath();
  ctx.arc(cx, ringCenterY, ringOuterR, 0, Math.PI * 2);
  ctx.arc(cx, ringCenterY, ringInnerR, 0, Math.PI * 2, true);
  ctx.closePath();
  ctx.fill();

  // "kg" label on the weight
  ctx.fillStyle = "#fff";
  const fontSize = Math.min(18, weightH * 0.55);
  ctx.font = `${fontSize}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("kg", cx, (wBY + wTY) / 2);

  // piston plate
  ctx.fillStyle = "#aaa";
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 1;
  ctx.fillRect(CYL_X, pistonY - 4, CYL_W, 8);
  ctx.strokeRect(CYL_X, pistonY - 4, CYL_W, 8);

  // gas particles
  ctx.fillStyle = tint;
  for (const p of particles) {
    const mag = Math.hypot(p.vx, p.vy) || 1;
    p.x += (p.vx / mag) * speed;
    p.y += (p.vy / mag) * speed;
    if (p.x < CYL_X + 3) { p.x = CYL_X + 3; p.vx = Math.abs(p.vx); }
    else if (p.x > CYL_X + CYL_W - 3) { p.x = CYL_X + CYL_W - 3; p.vx = -Math.abs(p.vx); }
    if (p.y < pistonY + 5) { p.y = pistonY + 5; p.vy = Math.abs(p.vy); }
    else if (p.y > CYL_BOTTOM - 3) { p.y = CYL_BOTTOM - 3; p.vy = -Math.abs(p.vy); }
    ctx.beginPath();
    ctx.arc(p.x, p.y, 2.4, 0, Math.PI * 2);
    ctx.fill();
  }
}

// ---- HUD: current P, V, T, n in the top margin, active one highlighted ------
function drawHud(ctx, s) {
  const rows = [
    ["P", `${s.P.toFixed(0)} kPa`],
    ["V", `${s.V.toFixed(1)} L`],
    ["T", `${s.T.toFixed(0)} K`],
    ["n", `${s.n.toFixed(1)} mol`],
  ];
  ctx.textBaseline = "middle";
  let y = 20;
  for (const [sym, val] of rows) {
    const on = s.active === sym;
    ctx.fillStyle = on ? GREEN : "#888";
    ctx.font = `${on ? "bold " : ""}13px sans-serif`;
    ctx.textAlign = "left";
    ctx.fillText(`${sym} =`, 12, y);
    ctx.textAlign = "right";
    ctx.fillText(val, W - 12, y);
    y += 21;
  }
}

// ---- render loop + encode ---------------------------------------------------
function render() {
  const timeline = buildTimeline();
  const canvas = createCanvas(W * SCALE, H * SCALE);
  const ctx = canvas.getContext("2d");

  const gif = GIFEncoder();
  const delay = Math.round(1000 / FPS);
  let palette = null;

  // Prime the particle field so frame 0 isn't sparse.
  for (let i = 0; i < 30; i++) {
    ctx.save();
    ctx.scale(SCALE, SCALE);
    drawFrame(ctx, timeline[0]);
    ctx.restore();
  }

  for (let i = 0; i < timeline.length; i++) {
    ctx.save();
    ctx.scale(SCALE, SCALE);
    drawFrame(ctx, timeline[i]);
    ctx.restore();

    const { data, width, height } = ctx.getImageData(0, 0, canvas.width, canvas.height);
    if (!palette) palette = quantize(data, 256);
    const index = applyPalette(data, palette);
    gif.writeFrame(index, width, height, { palette, delay });
  }
  gif.finish();

  mkdirSync(dirname(OUT), { recursive: true });
  const bytes = gif.bytes();
  writeFileSync(OUT, bytes);
  console.log(`wrote ${OUT}`);
  console.log(`frames=${timeline.length} size=${(bytes.length / 1024).toFixed(0)} KB dims=${canvas.width}x${canvas.height}`);
}

render();
