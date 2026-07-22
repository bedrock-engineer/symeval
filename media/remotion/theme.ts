// Shared design tokens for the SymEval promo, aligned with the Bedrock brand
// (matches the docs site). Fonts are IBM Plex, loaded locally via
// @remotion/google-fonts so the render stays deterministic.

import { loadFont as loadSans } from "@remotion/google-fonts/IBMPlexSans";
import { loadFont as loadCondensed } from "@remotion/google-fonts/IBMPlexSansCondensed";
import { loadFont as loadMono } from "@remotion/google-fonts/IBMPlexMono";

export const COLORS = {
  green: "#63805e", // primary
  greenDark: "#4b6647",
  greenDeep: "#213320", // headings / near-black on brand
  greenSoft: "#eeffe6", // faint panel fill
  line: "#d0e6c7", // hairline borders
  gray: "#868b85", // neutral / subtitles
  grayDeep: "#2c2e30",
  brown: "#998468", // numeric tokens
  teal: "#3a7380", // secondary accent
  dark: "#171719", // body text
  bg: "#ffffff",
};

// Load only the weights/subset the promo uses — keeps render-time font requests
// (and flakiness) down versus pulling every weight and script.
const { fontFamily: sans } = loadSans("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] });
const { fontFamily: condensed } = loadCondensed("normal", { weights: ["600"], subsets: ["latin"] });
const { fontFamily: mono } = loadMono("normal", { weights: ["400"], subsets: ["latin"] });

export const FONTS = {
  sans: `${sans}, system-ui, sans-serif`,
  heading: `${condensed}, ${sans}, system-ui, sans-serif`,
  mono: `${mono}, "SF Mono", Menlo, Consolas, monospace`,
};

export const VIDEO = {
  width: 1920,
  height: 1080,
  fps: 30,
};
